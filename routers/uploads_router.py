from fastapi import APIRouter,HTTPException,UploadFile,File
import uuid
from typing import List,Annotated
from config.aws_boto3 import s3, BUCKET_NAME
AWS_REGION = "us-east-1"
upload_router=APIRouter(prefix="/imagesuploads",tags=["imageuploads"])
@upload_router.post("/images")
async def upload_images(files: List[UploadFile]= File(...)):
    try:
        image_urls = []

        for file in files:
            ext = file.filename.split(".")[-1]
            key = f"products/{uuid.uuid4()}.{ext}"

            s3.upload_fileobj(
                file.file,
                BUCKET_NAME,
                key,
                ExtraArgs={"ContentType": file.content_type}
            )

            url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
            image_urls.append(url)

        return {"image_urls": image_urls}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get images by list of URLs (simply returns the URLs if they exist)
@upload_router.post("/get_images")
async def get_images(image_urls: List[str]):
    # In a real scenario, you might check if these images exist in S3
    # Here, just return the URLs
    return {"image_urls": image_urls}

@upload_router.get("/all_images")
async def get_all_images():
    try:
        image_urls = []
        # List all objects under the 'products/' prefix
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="products/")
        for obj in response.get("Contents", []):
            key = obj["Key"]
            url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
            image_urls.append(url)
        return {"image_urls": image_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Update images: replace old images with new ones (delete old, upload new)
@upload_router.put("/update_images")
async def update_images(
    old_image_urls: List[str] = None,
    files: List[UploadFile] = File(None)
):
    updated_image_urls = []
    # Delete old images if provided
    if old_image_urls:
        for url in old_image_urls:
            try:
                key = url.split(f".amazonaws.com/")[-1]
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
            except Exception as e:
                # Log error, but continue
                pass
    # Upload new images if provided
    if files:
        for file in files:
            ext = file.filename.split(".")[-1]
            key = f"products/{uuid.uuid4()}.{ext}"
            s3.upload_fileobj(
                file.file,
                BUCKET_NAME,
                key,
                ExtraArgs={"ContentType": file.content_type}
            )
            url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
            updated_image_urls.append(url)
    return {"image_urls": updated_image_urls}


# Delete images (one or multiple)
@upload_router.delete("/delete_images")
async def delete_images(image_urls: List[str]):
    deleted = []
    errors = []
    for url in image_urls:
        try:
            key = url.split(f".amazonaws.com/")[-1]
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)
            deleted.append(url)
        except Exception as e:
            errors.append({"url": url, "error": str(e)})
    return {"deleted": deleted, "errors": errors}