
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Annotated, Literal
from schemas.products_schema import product_data, all_products_data
from config.collection import products_collection, categories_collection
from models.products_model import Products, UpdateProduct
from datetime import datetime
from typing import Optional,List
import uuid
import re
import json
from bson import ObjectId
from config.aws_boto3 import s3, BUCKET_NAME
products_router = APIRouter(prefix="/products", tags=["Products"])
AWS_REGION = "us-east-1"
# Create product with image upload


# Create product (image upload handled by uploads_router, expects image_urls as input)
@products_router.post("/create_product")
async def create_product(
    product_name: str = Form(...),
    description: str = Form(...),
    business_type: Literal["retail", "wholesale"] = Form(...),
    category_id: str = Form(...),
    subcategory: Optional[str] = Form(None),
    pricing: str = Form(...),  # Expect JSON string
    is_active: Optional[bool] = Form(True),
    image_urls: Optional[str] = Form(None),  # JSON list of URLs
    admin_id: str = Form(...)
):
    # Parse pricing JSON string
    try:
        pricing_list = json.loads(pricing)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid pricing format. Must be JSON list.")

    # Parse image_urls JSON string
    urls = []
    if image_urls:
        try:
            urls = json.loads(image_urls)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image_urls format. Must be JSON list.")

    product_dict = {
        "product_name": product_name,
        "description": description,
        "images_url": urls,
        "business_type": business_type,
        "category_id": category_id,
        "subcategory": subcategory,
        "pricing": pricing_list,
        "is_active": is_active,
        "admin_id": admin_id
    }

    res = await products_collection.insert_one(product_dict)
    return {"message": "Successfully Inserted", "product_id": str(res.inserted_id), "images_url": urls}



# Get all products (optionally filter by admin_id)
@products_router.get("/all")
async def get_all_products(admin_id: Optional[str] = None):
    """
    Get all products. If admin_id is provided, only return products created by that admin.
    """
    query = {"admin_id": admin_id} if admin_id else {}
    products = await products_collection.find(query).to_list(1000)
    return all_products_data(products)
# Get all products for a specific admin
@products_router.get("/by-admin/{admin_id}")
async def get_products_by_admin(admin_id: str):
    """
    Get all products created by a specific admin.
    """
    products = await products_collection.find({"admin_id": admin_id}).to_list(1000)
    return all_products_data(products)

@products_router.get('/get_product/{product_id}')
async def get_product_by_id(product_id: str):
    try:
        res = await products_collection.find_one({"_id": ObjectId(product_id)})
        if not res:
            raise HTTPException(status_code=404, detail="Product not found.")
        return product_data(res)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product_id")
# Update product by id

# Update product (image upload/update handled by uploads_router, expects image_urls as input)

# Update product (image upload/update handled by uploads_router, expects image_urls as input)
@products_router.put("/update_product/{product_id}")
async def update_product(
    product_id: str,
    product_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    business_type: Optional[Literal["retail", "wholesale"]] = Form(None),
    category_id: Optional[str] = Form(None),
    subcategory: Optional[str] = Form(None),
    pricing: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    image_urls: Optional[str] = Form(None)  # JSON list of URLs
):
    update_data = {}
    # Fetch the current product to compare images
    current_product = await products_collection.find_one({"_id": ObjectId(product_id)})
    if not current_product:
        raise HTTPException(status_code=404, detail="Product not found.")

    old_images = current_product.get("images_url", [])
    new_images = None

    if product_name is not None:
        update_data["product_name"] = product_name
    if description is not None:
        update_data["description"] = description
    if business_type is not None:
        update_data["business_type"] = business_type
    if category_id is not None:
        update_data["category_id"] = category_id
    if pricing is not None:
        try:
            update_data["pricing"] = json.loads(pricing)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid pricing format. Must be JSON list.")
    if is_active is not None:
        update_data["is_active"] = is_active
    if subcategory is not None:
        update_data["subcategory"] = subcategory
    if image_urls is not None:
        try:
            new_images = json.loads(image_urls)
            update_data["images_url"] = new_images
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image_urls format. Must be JSON list.")

    # Delete removed images from S3
    if new_images is not None:
        removed_images = set(old_images) - set(new_images)
        for url in removed_images:
            try:
                key = url.split(f".amazonaws.com/")[-1]
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
            except Exception:
                pass

    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided.")
    res = await products_collection.update_one({"_id": ObjectId(product_id)}, {"$set": update_data})
    return {"message": "Product updated", "updated_fields": update_data}


# Delete product by id

# Delete product by id and its images from S3
@products_router.delete("/delete_product/{product_id}")
async def delete_product(product_id: str):
    product = await products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    # Delete all images from S3
    for url in product.get("images_url", []):
        try:
            key = url.split(f".amazonaws.com/")[-1]
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)
        except Exception:
            pass
    res = await products_collection.delete_one({"_id": ObjectId(product_id)})
    return {"message": "Product deleted and images removed from S3"}