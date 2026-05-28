from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from typing import List, Annotated, Optional, Literal
import uuid
from datetime import datetime
from config.rate_limiter import limiter, RATE_LIMITS
from models.issues_model import Issues, IssuesUploadHandler
from schemas.issues_schema import IssuesCreate, IssuesResponse

issues_router = APIRouter(prefix="/issues", tags=["issues"])


@issues_router.post("/create", response_model=IssuesResponse)
@limiter.limit(RATE_LIMITS["upload_write"])
async def create_issue(
    request: Request,
    order_id: str = Form(...),
    payment_id: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...),
    issue_type: str = Form(...),
    detailed_reason: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Create an issue with optional or required image uploads based on issue_type.
    
    - **Refund/Return**: Images are REQUIRED
    - **Replace Order**: Images are REQUIRED
    - **Cancel Order**: Images are OPTIONAL
    """
    try:
        # Validate issue_type
        if issue_type not in ["Refund/Return", "Cancel Order", "Replace Order"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid issue_type. Must be one of: 'Refund/Return', 'Cancel Order', 'Replace Order'"
            )
        
        # Check image requirements based on issue_type
        if issue_type in ["Refund/Return", "Replace Order"]:
            if not files or len(files) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Images are required for '{issue_type}'. Please upload at least one image."
                )
        
        image_urls = []
        
        # Upload images if provided
        if files and len(files) > 0:
            image_urls = IssuesUploadHandler.upload_issue_images(files)
        
        # Create issue data
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
        
        # Validate with schema
        issue = Issues(**issue_data)
        
        # Generate issue ID
        issue_id = str(uuid.uuid4())
        
        return IssuesResponse(
            issue_id=issue_id,
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
async def get_all_issue_images(request: Request):
    """Get all issue images from the issues_folder in S3"""
    try:
        image_urls = IssuesUploadHandler.get_all_issue_images()
        return {"image_urls": image_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@issues_router.delete("/delete_images")
@limiter.limit(RATE_LIMITS["upload_write"])
async def delete_issue_images(request: Request, image_urls: List[str]):
    """Delete specific issue images from S3"""
    try:
        IssuesUploadHandler.delete_issue_images(image_urls)
        return {"message": "Images deleted successfully", "deleted_count": len(image_urls)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    status: Literal["Pending", "Solved"]
):
    """
    Update the status of an issue
    
    Parameters:
    - issue_id: The unique identifier of the issue
    - status: New status - must be either "Pending" or "Solved"
    
    Returns:
    - Updated issue status information
    """
    try:
        if status not in ["Pending", "Solved"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Must be either 'Pending' or 'Solved'"
            )
        
        return {
            "issue_id": issue_id,
            "status": status,
            "message": f"Issue status updated to '{status}' successfully",
            "updated_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update issue status: {str(e)}")


@issues_router.get("/pending", response_model=List[IssuesResponse])
@limiter.limit(RATE_LIMITS["upload_read"])
async def get_pending_issues(request: Request):
    """
    Get all issues with 'Pending' status
    
    Returns:
    - List of all pending issues with their details
    """
    try:
        # Note: This endpoint is structured for database integration
        # Currently returns empty list - integrate with your database layer
        
        # Example for MongoDB integration:
        # pending_issues = await issues_collection.find({"status": "Pending"}).to_list(None)
        
        # Placeholder response structure:
        pending_issues = []
        
        return pending_issues
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pending issues: {str(e)}")


@issues_router.get("/by_status/{status}", response_model=List[IssuesResponse])
@limiter.limit(RATE_LIMITS["upload_read"])
async def get_issues_by_status(
    request: Request,
    status: Literal["Pending", "Solved"]
):
    """
    Get all issues by specific status
    
    Parameters:
    - status: Filter by status ("Pending" or "Solved")
    
    Returns:
    - List of issues matching the specified status
    """
    try:
        # Note: This endpoint is structured for database integration
        # Example for MongoDB integration:
        # issues = await issues_collection.find({"status": status}).to_list(None)
        # return [IssuesResponse(**issue) for issue in issues]
        
        # Placeholder response:
        issues = []
        
        return issues
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve issues: {str(e)}")
