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

def address_data(address: dict | None) -> dict:
    safe_address = address or {}
    return {
        "name": safe_address.get("name"),
        "mobile": safe_address.get("mobile"),
        "address_line": safe_address.get("address_line"),
        "city": safe_address.get("city"),
        "country": safe_address.get("country"),
        "pincode": safe_address.get("pincode"),
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


def single_order_data(order: dict) -> dict:
    """Returns full details of a single order including all fields."""
    return {
        "id": str(order.get("_id")),
        "custom_order_id": order.get("custom_order_id"),
        "user_email": order.get("user_email"),
        "guest_id": order.get("guest_id"),
        # Items
        "items": [order_item_data(i) for i in order.get("items", [])],
        # Addresses (full, including state)
        "shipping_address": {
            "name": (order.get("shipping_address") or {}).get("name"),
            "mobile": (order.get("shipping_address") or {}).get("mobile"),
            "address_line": (order.get("shipping_address") or {}).get("address_line"),
            "city": (order.get("shipping_address") or {}).get("city"),
            "state": (order.get("shipping_address") or {}).get("state"),
            "country": (order.get("shipping_address") or {}).get("country"),
            "pincode": (order.get("shipping_address") or {}).get("pincode"),
        },
        "billing_address": {
            "name": (order.get("billing_address") or {}).get("name"),
            "mobile": (order.get("billing_address") or {}).get("mobile"),
            "address_line": (order.get("billing_address") or {}).get("address_line"),
            "city": (order.get("billing_address") or {}).get("city"),
            "state": (order.get("billing_address") or {}).get("state"),
            "country": (order.get("billing_address") or {}).get("country"),
            "pincode": (order.get("billing_address") or {}).get("pincode"),
        },
        # Pricing
        "subtotal": order.get("subtotal"),
        "coupon_code": order.get("coupon_code"),
        "discount_amount": order.get("discount_amount"),
        "gst_amount": order.get("gst_amount"),
        "delivery_charges": order.get("delivery_charges"),
        "grand_total": order.get("grand_total"),
        # Payment & Status
        "razorpay_order_id": order.get("razorpay_order_id"),
        "razorpay_payment_id": order.get("razorpay_payment_id"),
        "order_status": order.get("order_status"),
        "payment_status": order.get("payment_status"),
        # Timestamps
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at"),
    }
