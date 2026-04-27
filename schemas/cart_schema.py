def cart_item_data(item: dict) -> dict:
    """Serialize a single cart item dict."""
    return {
        "product_id": item.get("product_id"),
        "product_name": item.get("product_name"),
        "image_url": item.get("image_url"),
        "weight": item.get("weight"),
        "price": item.get("price"),
        "quantity": item.get("quantity"),
        "business_type": item.get("business_type"),
        "line_total": round(item.get("price", 0) * item.get("quantity", 0), 2),
    }


def cart_data(cart: dict) -> dict:
    """Serialize a full cart document from MongoDB."""
    items = [cart_item_data(i) for i in cart.get("items", [])]
    subtotal = round(sum(i["line_total"] for i in items), 2)
    discount = round(cart.get("discount_amount", 0.0), 2)

    return {
        "id": str(cart.get("_id", "")),
        "user_email": cart.get("user_email"),
        "guest_id": cart.get("guest_id"),
        "items": items,
        "item_count": len(items),
        "subtotal": subtotal,
        "coupon_code": cart.get("coupon_code"),
        "discount_amount": discount,
        "total_preview": round(subtotal - discount, 2),
        "updated_at": cart.get("updated_at"),
        "created_at": cart.get("created_at"),
    }
