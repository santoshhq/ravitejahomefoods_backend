from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import json
import uuid

from pydantic import ValidationError
from models.reviews_model import Reviews, ReviewUpdate
from config.collection import reviews_collection
from config.aws_boto3 import s3, BUCKET_NAME
from config.rate_limiter import limiter, RATE_LIMITS
from schemas.reviews_schema import review_data, all_reviews_data

reviews_router = APIRouter(prefix="/reviews", tags=["Reviews"])
AWS_REGION = "us-east-1"


def parse_review_form(
	product_id: str = Form(...),
	rating: int = Form(...),
	review_title: str = Form(...),
	review_content: str = Form(...),
	display_name: str = Form(...),
	email_address: str = Form(...),
	mobile_number: str = Form(...),
	is_active: bool = Form(True),
):
	try:
		return Reviews(
			product_id=product_id,
			rating=rating,
			review_title=review_title,
			review_content=review_content,
			display_name=display_name,
			email_address=email_address,
			mobile_number=mobile_number,
			is_active=is_active,
		)
	except ValidationError as exc:
		raise HTTPException(status_code=400, detail=exc.errors()) from exc


def parse_review_update_form(
	rating: Optional[int] = Form(None),
	review_title: Optional[str] = Form(None),
	review_content: Optional[str] = Form(None),
	display_name: Optional[str] = Form(None),
	email_address: Optional[str] = Form(None),
	mobile_number: Optional[str] = Form(None),
	is_active: Optional[bool] = Form(None),
):
	try:
		return ReviewUpdate(
			rating=rating,
			review_title=review_title,
			review_content=review_content,
			display_name=display_name,
			email_address=email_address,
			mobile_number=mobile_number,
			is_active=is_active,
		)
	except ValidationError as exc:
		raise HTTPException(status_code=400, detail=exc.errors()) from exc


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


@reviews_router.post("/create_review", status_code=201)
@limiter.limit(RATE_LIMITS["review_write"])
async def create_review(
	request: Request,
	review: Reviews = Depends(parse_review_form),
	files: Optional[List[UploadFile]] = File(None),
):
	review_images_url = await _upload_review_images(files)
	payload = {
		"product_id": review.product_id,
		"rating": review.rating,
		"review_title": review.review_title,
		"review_content": review.review_content,
		"review_images_url": review_images_url,
		"display_name": review.display_name,
		"email_address": review.email_address,
		"mobile_number": review.mobile_number,
		"is_active": True if review.is_active is None else review.is_active,
		"created_at": datetime.utcnow().isoformat(),
		"updated_at": None,
	}
	res = await reviews_collection.insert_one(payload)
	created = await reviews_collection.find_one({"_id": ObjectId(res.inserted_id)})
	return {
		"message": "Review created",
		"data": review_data(created) if created else {"id": str(res.inserted_id)},
	}


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
	ratings = [review.get("rating") for review in reviews if isinstance(review.get("rating"), (int, float))]
	avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
	return {
		"count": len(reviews),
		"avg_rating": avg_rating,
		"data": all_reviews_data(reviews),
	}


@reviews_router.get("/{review_id}")
@limiter.limit(RATE_LIMITS["review_read"])
async def get_review_by_id(request: Request, review_id: str):
	try:
		review = await reviews_collection.find_one({"_id": ObjectId(review_id)})
		if not review:
			raise HTTPException(status_code=404, detail="Review not found.")
		return {"data": review_data(review)}
	except Exception:
		raise HTTPException(status_code=400, detail="Invalid review_id")


@reviews_router.put("/update_review/{review_id}")
@limiter.limit(RATE_LIMITS["review_write"])
async def update_review(
	request: Request,
	review_id: str,
	review_update: ReviewUpdate = Depends(parse_review_update_form),
	files: Optional[List[UploadFile]] = File(None),
):
	review = await reviews_collection.find_one({"_id": ObjectId(review_id)})
	if not review:
		raise HTTPException(status_code=404, detail="Review not found.")

	update_data = review_update.model_dump(exclude_none=True)

	if files is not None:
		_delete_s3_images(review.get("review_images_url", []))
		update_data["review_images_url"] = await _upload_review_images(files)

	if not update_data:
		raise HTTPException(status_code=400, detail="No update fields provided.")

	update_data["updated_at"] = datetime.utcnow().isoformat()
	await reviews_collection.update_one({"_id": ObjectId(review_id)}, {"$set": update_data})
	updated = await reviews_collection.find_one({"_id": ObjectId(review_id)})
	return {"message": "Review updated", "data": review_data(updated) if updated else None}


@reviews_router.delete("/delete_review/{review_id}")
@limiter.limit(RATE_LIMITS["review_write"])
async def delete_review(request: Request, review_id: str):
	review = await reviews_collection.find_one({"_id": ObjectId(review_id)})
	if not review:
		raise HTTPException(status_code=404, detail="Review not found.")
	_delete_s3_images(review.get("review_images_url", []))
	await reviews_collection.delete_one({"_id": ObjectId(review_id)})
	return {"message": "Review deleted", "data": {"id": review_id}}


@reviews_router.delete("/delete_by_product/{product_id}")
@limiter.limit(RATE_LIMITS["review_write"])
async def delete_reviews_by_product(request: Request, product_id: str):
	reviews = await reviews_collection.find({"product_id": product_id}).to_list(1000)
	for review in reviews:
		_delete_s3_images(review.get("review_images_url", []))
	result = await reviews_collection.delete_many({"product_id": product_id})
	return {
		"message": "Reviews deleted",
		"deleted_count": result.deleted_count,
		"product_id": product_id,
	}
