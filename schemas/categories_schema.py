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
		"admin_id": category.get("admin_id"),
	}


def all_data(categories) -> list:
	return [indiviual_data(category) for category in categories]

def category_serializer(data: dict) -> dict:
    """Serialize a single category."""
    return {
        "id": str(data.get("_id")),
        "name": data.get("name"),
    }


def all_categories(categories: list) -> list:
    """Serialize all categories."""
    return [category.get("name") for category in categories if category.get("name")]
