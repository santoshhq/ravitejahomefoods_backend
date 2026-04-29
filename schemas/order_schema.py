def order_item_data(item: dict) -> dict:
    return {
        "product_id": item.get("product_id"),
        "product_name": item.get("product_name"),
        "image_url": item.get("image_url"),
        "weight": item.get("weight"),
        "price": item.get("price"),
        "quantity": item.get("quantity"),
        "business_type": item.get("business_type"),
    }

def address_data(address: dict) -> dict:
    return {
        "name": address.get("name"),
        "mobile": address.get("mobile"),
        "address_line": address.get("address_line"),
        "city": address.get("city"),
        "country": address.get("country"),
        "pincode": address.get("pincode"),
    }

def order_data(order: dict) -> dict:
    return {
        "id": str(order.get("_id")),
        "user_email": order.get("user_email"),
        "items": [order_item_data(i) for i in order.get("items", [])],
        "shipping_address": address_data(order.get("shipping_address", {})),
        "billing_address": address_data(order.get("billing_address", {})),
        "subtotal": order.get("subtotal"),
        "coupon_code": order.get("coupon_code"),
        "discount_amount": order.get("discount_amount"),
        "gst_amount": order.get("gst_amount"),
        "delivery_charges": order.get("delivery_charges"),
        "grand_total": order.get("grand_total"),
        "razorpay_order_id": order.get("razorpay_order_id"),
        "order_status": order.get("order_status"),
        "payment_status": order.get("payment_status"),
        "created_at": order.get("created_at"),
    }

def all_orders_data(orders: list) -> list:
    return [order_data(o) for o in orders]
