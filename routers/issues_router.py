from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Query
from typing import List, Annotated, Optional, Literal
from datetime import datetime
from config.rate_limiter import limiter, RATE_LIMITS
from config.collection import issues_collection
from models.issues_model import Issues, IssuesUploadHandler
from schemas.issues_schema import IssuesCreate, IssuesResponse
from bson import ObjectId
from bson.errors import InvalidId

issues_router = APIRouter(prefix="/issues", tags=["issues"])


def parse_object_id(issue_id: str) -> ObjectId:
    """Helper to parse and validate an ObjectId string."""
    try:
        return ObjectId(issue_id)
    except (InvalidId, Exception):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid issue ID format: '{issue_id}'. Must be a valid MongoDB ObjectId."
        )


def format_issue(issue: dict) -> IssuesResponse:
    """Helper to convert a MongoDB document to IssuesResponse."""
    return IssuesResponse(
        issue_id=str(issue["_id"]),
        order_id=issue["order_id"],
        payment_id=issue.get("payment_id"),
        email=issue["email"],
        mobile=issue.get("mobile"),
        issue_type=issue["issue_type"],
        detailed_reason=issue["detailed_reason"],
        image_urls=issue.get("image_urls"),
        status=issue["status"]
    )


@issues_router.post("/create", response_model=IssuesResponse, status_code=201)
@limiter.limit(RATE_LIMITS["upload_write"])
async def create_issue(
    request: Request,
    order_id: str = Form(...),
    payment_id: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...),
    issue_type: str = Form(...),
    detailed_reason: str = Form(...)
):
    """
    Create an issue with optional or required image uploads based on issue_type.
    
    - **Refund/Return**: Images are REQUIRED
    - **Replace Order**: Images are REQUIRED
    - **Cancel Order**: Images are OPTIONAL
    
    Returns the created issue with its MongoDB ObjectId as `issue_id`.
    """
    try:
        # Parse multipart form data manually to handle empty files
        form_data = await request.form()
        
        # Get files and filter out empty ones
        files = form_data.getlist("files")
        valid_files = []
        
        for file in files:
            if hasattr(file, 'filename') and file.filename and file.filename.strip():
                valid_files.append(file)
        
        # Validate issue_type
        if issue_type not in ["Refund/Return", "Cancel Order", "Replace Order"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid issue_type. Must be one of: 'Refund/Return', 'Cancel Order', 'Replace Order'"
            )
        if issue_type in ["Refund/Return", "Replace Order"]:
            if not valid_files or len(valid_files) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Images are required for '{issue_type}'. Please upload at least one image."
                )
        
        image_urls = []
        
        # Upload images to S3 if provided
        if valid_files and len(valid_files) > 0:
            image_urls = IssuesUploadHandler.upload_issue_images(valid_files)
        
        # Build issue data
        issue_data = {
            "order_id": order_id,
            "payment_id": payment_id,
            "email": email,
            "mobile": mobile,
            "issue_type": issue_type,
            "detailed_reason": detailed_reason,
            "image_urls": image_urls if image_urls else None,
            "status": "Pending"
        }
        
        # Validate with Pydantic model
        issue = Issues(**issue_data)
        
        # Insert into MongoDB — use _id (ObjectId) as the unique identifier
        # mode='json' ensures AnyHttpUrl and EmailStr fields are serialized
        # as plain strings (not Pydantic objects), which MongoDB can encode
        doc_to_insert = issue.model_dump(mode='json')
        doc_to_insert["created_at"] = datetime.utcnow()
        result = await issues_collection.insert_one(doc_to_insert)
        
        return IssuesResponse(
            issue_id=str(result.inserted_id),
            order_id=issue.order_id,
            email=issue.email,
            issue_type=issue.issue_type,
            detailed_reason=issue.detailed_reason,
            image_urls=issue.image_urls,
            status=issue.status
        )
        
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create issue: {str(e)}")


@issues_router.get("/all_images")
@limiter.limit(RATE_LIMITS["upload_list"])
async def get_all_issue_images(
    request: Request,
    prefix: Optional[str] = Query(None, description="Filter by S3 folder prefix")
):
    """
    Get all issue images from S3
    
    Parameters:
    - prefix: Optional S3 prefix to filter images by folder
    
    Returns:
    - List of all issue image URLs
    """
    try:
        image_urls = IssuesUploadHandler.get_all_issue_images()
        
        if prefix:
            image_urls = [url for url in image_urls if prefix in url]
        
        return {
            "image_urls": image_urls,
            "count": len(image_urls)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve images: {str(e)}")


@issues_router.get("/by-order/{order_id}", response_model=List[IssuesResponse])
@limiter.limit(RATE_LIMITS["upload_read"])
async def get_issues_by_order(request: Request, order_id: str):
    """
    Get all issues for a specific order
    
    Parameters:
    - order_id: The order ID to search for
    
    Returns:
    - List of issues associated with the order
    """
    try:
        issues = await issues_collection.find({"order_id": order_id}).to_list(None)
        return [format_issue(issue) for issue in issues]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve issues: {str(e)}")


@issues_router.delete("/delete_images")
@limiter.limit(RATE_LIMITS["upload_write"])
async def delete_issue_images(
    request: Request,
    image_urls: List[str] = Query(...)
):
    """
    Delete specific issue images from S3
    
    Parameters:
    - image_urls: List of S3 image URLs to delete
    
    Returns:
    - Confirmation message with count of deleted images
    """
    try:
        if not image_urls or len(image_urls) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one image URL must be provided"
            )
        
        IssuesUploadHandler.delete_issue_images(image_urls)
        return {
            "message": "Images deleted successfully",
            "deleted_count": len(image_urls),
            "deleted_urls": image_urls
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete images: {str(e)}")


@issues_router.get("/validate_requirement/{issue_type}")
async def get_image_requirement(issue_type: str):
    """
    Check image upload requirements for a specific issue type
    
    Returns:
    - is_required: True if images are required, False if optional
    - message: Explanation of requirement
    """
    if issue_type not in ["Refund/Return", "Cancel Order", "Replace Order"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid issue_type"
        )
    
    if issue_type in ["Refund/Return", "Replace Order"]:
        return {
            "issue_type": issue_type,
            "is_required": True,
            "message": f"Images are REQUIRED for {issue_type}"
        }
    else:  # Cancel Order
        return {
            "issue_type": issue_type,
            "is_required": False,
            "message": f"Images are OPTIONAL for {issue_type}"
        }


@issues_router.patch("/update_status/{issue_id}")
@limiter.limit(RATE_LIMITS["upload_write"])
async def update_issue_status(
    request: Request,
    issue_id: str,
    status: Literal["Pending", "Solved"] = Query(...)
):
    """
    Update the status of an issue
    
    Parameters:
    - issue_id: MongoDB ObjectId of the issue
    - status: New status - must be either "Pending" or "Solved"
    
    Returns:
    - Updated issue status information with timestamp
    """
    try:
        oid = parse_object_id(issue_id)

        # Check if issue exists
        existing = await issues_collection.find_one({"_id": oid})
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Issue with ID '{issue_id}' not found"
            )

        updated_at = datetime.utcnow()

        # Update status in MongoDB
        result = await issues_collection.update_one(
            {"_id": oid},
            {"$set": {"status": status, "updated_at": updated_at}}
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=400,
                detail=f"Issue status is already '{status}', no changes made"
            )

        return {
            "issue_id": issue_id,
            "status": status,
            "message": f"Issue status updated to '{status}' successfully",
            "updated_at": updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update issue status: {str(e)}")


@issues_router.get("/pending", response_model=List[IssuesResponse])
@limiter.limit(RATE_LIMITS["upload_read"])
async def get_pending_issues(
    request: Request,
    issue_type: Optional[str] = Query(None, description="Filter by issue type"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get all issues with 'Pending' status
    
    Parameters:
    - issue_type: Optional filter by issue type (Refund/Return, Cancel Order, Replace Order)
    - limit: Maximum number of results (default: 10, max: 100)
    - skip: Number of results to skip for pagination (default: 0)
    
    Returns:
    - List of all pending issues with their details
    """
    try:
        query = {"status": "Pending"}
        if issue_type:
            if issue_type not in ["Refund/Return", "Cancel Order", "Replace Order"]:
                raise HTTPException(status_code=400, detail="Invalid issue_type. Must be one of: 'Refund/Return', 'Cancel Order', 'Replace Order'")
            query["issue_type"] = issue_type
        
        pending_issues = await issues_collection.find(query).skip(skip).limit(limit).to_list(None)
        return [format_issue(issue) for issue in pending_issues]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pending issues: {str(e)}")


@issues_router.get("/by_status/{status}", response_model=List[IssuesResponse])
@limiter.limit(RATE_LIMITS["upload_read"])
async def get_issues_by_status(
    request: Request,
    status: Literal["Pending", "Solved"],
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip for pagination")
):
    """
    Get all issues by specific status
    
    Parameters:
    - status: Filter by status ("Pending" or "Solved")
    - limit: Maximum number of results (default: 10, max: 100)
    - skip: Number of results to skip for pagination (default: 0)
    
    Returns:
    - List of issues matching the specified status
    """
    try:
        issues = await issues_collection.find({"status": status}).skip(skip).limit(limit).to_list(None)
        return [format_issue(issue) for issue in issues]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve issues: {str(e)}")


@issues_router.get("/{issue_id}", response_model=IssuesResponse)
@limiter.limit(RATE_LIMITS["upload_read"])
async def get_issue(request: Request, issue_id: str):
    """
    Get a specific issue by its MongoDB ObjectId
    
    Parameters:
    - issue_id: MongoDB ObjectId of the issue
    
    Returns:
    - Issue details including order info, issue type, status, and images
    """
    try:
        oid = parse_object_id(issue_id)
        issue = await issues_collection.find_one({"_id": oid})
        if not issue:
            raise HTTPException(
                status_code=404,
                detail=f"Issue with ID '{issue_id}' not found"
            )
        return format_issue(issue)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve issue: {str(e)}")


@issues_router.get("/{issue_id}", response_model=IssuesResponse)
@limiter.limit(RATE_LIMITS["upload_read"])
async def get_issue(request: Request, issue_id: str):
    """
    Get a specific issue by its MongoDB ObjectId
    
    Parameters:
    - issue_id: MongoDB ObjectId of the issue
    
    Returns:
    - Issue details including order info, issue type, status, and images
    """
    try:
        oid = parse_object_id(issue_id)
        issue = await issues_collection.find_one({"_id": oid})
        if not issue:
            raise HTTPException(
                status_code=404,
                detail=f"Issue with ID '{issue_id}' not found"
            )
        return format_issue(issue)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve issue: {str(e)}")

@issues_router.delete("/{issue_id}")
@limiter.limit(RATE_LIMITS["upload_write"])
async def delete_issue(request: Request, issue_id: str):
    """
    Delete a specific issue by its MongoDB ObjectId
    
    Parameters:
    - issue_id: MongoDB ObjectId of the issue
    
    Returns:
    - Confirmation message
    """
    try:
        oid = parse_object_id(issue_id)
        
        # Check if the issue exists first
        existing_issue = await issues_collection.find_one({"_id": oid})
        if not existing_issue:
            raise HTTPException(
                status_code=404,
                detail=f"Issue with ID '{issue_id}' not found"
            )
            
        # Optional: You could also delete associated images from S3 here if needed
        # if existing_issue.get("image_urls"):
        #     IssuesUploadHandler.delete_issue_images(existing_issue["image_urls"])
            
        result = await issues_collection.delete_one({"_id": oid})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete the issue."
            )
            
        return {
            "message": f"Issue '{issue_id}' successfully deleted.",
            "deleted": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete issue: {str(e)}")
