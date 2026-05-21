def pricing_data(pricing_list):
    """Serialize a list of Pricing objects or dicts to a list of dicts."""
    if pricing_list is None:
        return []
    if not isinstance(pricing_list, list):
        return [
            {
                "weight": None,
                "price": pricing_list,
                "stock": None,
            }
        ]
    result = []
    for item in pricing_list or []:
        if isinstance(item, dict):
            result.append({
                "weight": item.get("weight"),
                "price": item.get("price"),
                "stock": item.get("stock"),
            })
        else:
            # If item is a Pydantic model
            result.append({
                "weight": getattr(item, "weight", None),
                "price": getattr(item, "price", None),
                "stock": getattr(item, "stock", None),
            })
    return result

def product_data(product) -> dict:
    """Serialize a single Products object or dict to a dict for response."""
    return {
        "id": str(product.get("_id", "")),
        "product_name": product.get("product_name"),
        "description": product.get("description"),
        "images_url": product.get("images_url", []),
        "business_type": product.get("business_type"),
        "category_id": product.get("category_id"),
        "subcategory": product.get("subcategory"),
        "pricing": pricing_data(product.get("pricing")),
        "is_active": product.get("is_active", True),
        "admin_id": product.get("admin_id"),
    }

def all_products_data(products) -> list:
    return [product_data(product) for product in products]


    
