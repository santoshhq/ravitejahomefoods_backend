def review_data(review: dict) -> dict:
	return {
		"id": str(review.get("_id", "")),
		"product_id": review.get("product_id"),
		"rating": review.get("rating"),
		"review_title": review.get("review_title"),
		"review_content": review.get("review_content"),
		"review_images_url": review.get("review_images_url", []),
		"display_name": review.get("display_name"),
		"email_address": review.get("email_address"),
		"mobile_number": review.get("mobile_number"),
		"is_active": review.get("is_active", True),
		"created_at": review.get("created_at"),
		"updated_at": review.get("updated_at"),
	}


def all_reviews_data(reviews: list) -> list:
	return [review_data(review) for review in reviews]
