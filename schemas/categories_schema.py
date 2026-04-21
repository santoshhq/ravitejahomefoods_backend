def _subcategory_data(subcategory) -> dict:
	if isinstance(subcategory, dict):
		return {"name": subcategory.get("name")}
	return {"name": subcategory}


def indiviual_data(category) -> dict:
	subcategories = category.get("subcategory") or []
	return {
		"id": str(category["_id"]),
		"name": category.get("name"),
		"business_type": category.get("business_type"),
		"subcategory": [_subcategory_data(item) for item in subcategories],
	}


def all_data(categories) -> list:
	return [indiviual_data(category) for category in categories]
