from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import json
import uuid

from config.collection import reviews_collection
from config.aws_boto3 import s3, BUCKET_NAME
from config.rate_limiter import limiter, RATE_LIMITS
from schemas.reviews_schema import review_data, all_reviews_data

reviews_router = APIRouter(prefix="/reviews", tags=["Reviews"])
AWS_REGION = "us-east-1"


async def _upload_review_images(files: Optional[List[UploadFile]]) -> list:
	image_urls = []
	if not files:
		return image_urls
	for file in files:
		ext = file.filename.split(".")[-1]
		key = f"reviews/{uuid.uuid4()}.{ext}"
		s3.upload_fileobj(
			file.file,
			BUCKET_NAME,
			key,
			ExtraArgs={"ContentType": file.content_type},
		)
		url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
		image_urls.append(url)
	return image_urls


def _delete_s3_images(image_urls: list) -> None:
	for url in image_urls or []:
		try:
			key = url.split(f".amazonaws.com/")[-1]
			s3.delete_object(Bucket=BUCKET_NAME, Key=key)
		except Exception:
			pass


@reviews_router.post("/create_review")
@limiter.limit(RATE_LIMITS["review_write"])
async def create_review(
	request: Request,
	product_id: str = Form(...),
	rating: int = Form(...),
	review_title: str = Form(...),
	review_content: str = Form(...),
	display_name: str = Form(...),
	email_address: str = Form(...),
	mobile_number: str = Form(...),
	is_active: Optional[bool] = Form(True),
	files: Optional[List[UploadFile]] = File(None),
):
	review_images_url = await _upload_review_images(files)
	payload = {
		"product_id": product_id,
		"rating": rating,
		"review_title": review_title,
		"review_content": review_content,
		"review_images_url": review_images_url,
		"display_name": display_name,
		"email_address": email_address,
		"mobile_number": mobile_number,
		"is_active": True if is_active is None else is_active,
		"created_at": datetime.utcnow().isoformat(),
		"updated_at": None,
	}
	res = await reviews_collection.insert_one(payload)
	return {"message": "Review created", "review_id": str(res.inserted_id)}


@reviews_router.get("/product/{product_id}")
@limiter.limit(RATE_LIMITS["review_read"])
async def get_reviews_by_product(
	request: Request,
	product_id: str,
	is_active: Optional[bool] = True,
):
	query = {"product_id": product_id}
	if is_active is not None:
		query["is_active"] = is_active
	reviews = await reviews_collection.find(query).to_list(1000)
	return all_reviews_data(reviews)


@reviews_router.get("/{review_id}")
@limiter.limit(RATE_LIMITS["review_read"])
async def get_review_by_id(request: Request, review_id: str):
	try:
		review = await reviews_collection.find_one({"_id": ObjectId(review_id)})
		if not review:
			raise HTTPException(status_code=404, detail="Review not found.")
		return review_data(review)
	except Exception:
		raise HTTPException(status_code=400, detail="Invalid review_id")


@reviews_router.put("/update_review/{review_id}")
@limiter.limit(RATE_LIMITS["review_write"])
async def update_review(
	request: Request,
	review_id: str,
	rating: Optional[int] = Form(None),
	review_title: Optional[str] = Form(None),
	review_content: Optional[str] = Form(None),
	display_name: Optional[str] = Form(None),
	email_address: Optional[str] = Form(None),
	mobile_number: Optional[str] = Form(None),
	is_active: Optional[bool] = Form(None),
	files: Optional[List[UploadFile]] = File(None),
):
	review = await reviews_collection.find_one({"_id": ObjectId(review_id)})
	if not review:
		raise HTTPException(status_code=404, detail="Review not found.")

	update_data = {}
	if rating is not None:
		update_data["rating"] = rating
	if review_title is not None:
		update_data["review_title"] = review_title
	if review_content is not None:
		update_data["review_content"] = review_content
	if display_name is not None:
		update_data["display_name"] = display_name
	if email_address is not None:
		update_data["email_address"] = email_address
	if mobile_number is not None:
		update_data["mobile_number"] = mobile_number
	if is_active is not None:
		update_data["is_active"] = is_active

	if files is not None:
		_delete_s3_images(review.get("review_images_url", []))
		update_data["review_images_url"] = await _upload_review_images(files)

	if not update_data:
		raise HTTPException(status_code=400, detail="No update fields provided.")

	update_data["updated_at"] = datetime.utcnow().isoformat()
	await reviews_collection.update_one({"_id": ObjectId(review_id)}, {"$set": update_data})
	return {"message": "Review updated"}


@reviews_router.delete("/delete_review/{review_id}")
@limiter.limit(RATE_LIMITS["review_write"])
async def delete_review(request: Request, review_id: str):
	review = await reviews_collection.find_one({"_id": ObjectId(review_id)})
	if not review:
		raise HTTPException(status_code=404, detail="Review not found.")
	_delete_s3_images(review.get("review_images_url", []))
	await reviews_collection.delete_one({"_id": ObjectId(review_id)})
	return {"message": "Review deleted"}


@reviews_router.delete("/delete_by_product/{product_id}")
@limiter.limit(RATE_LIMITS["review_write"])
async def delete_reviews_by_product(request: Request, product_id: str):
	reviews = await reviews_collection.find({"product_id": product_id}).to_list(1000)
	for review in reviews:
		_delete_s3_images(review.get("review_images_url", []))
	result = await reviews_collection.delete_many({"product_id": product_id})
	return {"message": "Reviews deleted", "deleted_count": result.deleted_count}
