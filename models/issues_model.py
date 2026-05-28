from pydantic import BaseModel, Field, EmailStr, AnyHttpUrl, field_validator
from typing import List, Literal, Optional
import uuid
from config.aws_boto3 import s3, BUCKET_NAME

AWS_REGION = "us-east-1"
ISSUES_FOLDER = "issues_folder"


class Issues(BaseModel):
    order_id: str = Field(..., min_length=1)
    payment_id: str = Field(..., min_length=1)
    email: EmailStr = Field(...)
    mobile: str = Field(..., min_length=10)
    issue_type: Literal["Refund/Return", "Cancel Order", "Replace Order"]
    detailed_reason: str = Field(..., min_length=10)
    image_urls: Optional[List[AnyHttpUrl]] = None
    status: Literal["Pending", "Solved"] = "Pending"

    @field_validator("image_urls")
    @classmethod
    def validate_images(cls, v, info):
        """
        Validate images based on issue_type:
        - Required for "Refund/Return" and "Replace Order"
        - Optional for "Cancel Order"
        """
        issue_type = info.data.get("issue_type")
        
        if issue_type in ["Refund/Return", "Replace Order"]:
            if not v or len(v) == 0:
                raise ValueError(
                    f"Images are required for '{issue_type}'. Please upload at least one image."
                )
        
        return v

    class Config:
        from_attributes = True


class IssuesUploadHandler:
    """Handle S3 uploads for issues"""
    
    @staticmethod
    def upload_issue_images(files: List) -> List[str]:
        """
        Upload issue images to S3 in the issues_folder
        
        Args:
            files: List of UploadFile objects
            
        Returns:
            List of S3 URLs for uploaded images
        """
        image_urls = []
        
        try:
            for file in files:
                ext = file.filename.split(".")[-1]
                key = f"{ISSUES_FOLDER}/{uuid.uuid4()}.{ext}"
                
                s3.upload_fileobj(
                    file.file,
                    BUCKET_NAME,
                    key,
                    ExtraArgs={"ContentType": file.content_type}
                )
                
                url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
                image_urls.append(url)
                
        except Exception as e:
            raise Exception(f"Failed to upload issue images: {str(e)}")
        
        return image_urls

    @staticmethod
    def delete_issue_images(image_urls: List[str]) -> None:
        """
        Delete issue images from S3
        
        Args:
            image_urls: List of S3 URLs to delete
        """
        try:
            for url in image_urls:
                key = url.split(f".amazonaws.com/")[-1]
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
        except Exception as e:
            raise Exception(f"Failed to delete issue images: {str(e)}")

    @staticmethod
    def get_all_issue_images() -> List[str]:
        """
        Get all issue images from S3
        
        Returns:
            List of all issue image URLs in the issues_folder
        """
        image_urls = []
        
        try:
            response = s3.list_objects_v2(
                Bucket=BUCKET_NAME, 
                Prefix=f"{ISSUES_FOLDER}/"
            )
            
            for obj in response.get("Contents", []):
                key = obj["Key"]
                url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
                image_urls.append(url)
                
        except Exception as e:
            raise Exception(f"Failed to retrieve issue images: {str(e)}")
        
        return image_urls

    