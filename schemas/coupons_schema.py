from datetime import datetime


def coupon_data(coupon) -> dict:
    expire_date = coupon.get("expire_date")
    if isinstance(expire_date, datetime):
        expire_date = expire_date.isoformat()

    return {
        "id": str(coupon.get("_id", "")),
        "couponcode": coupon.get("couponcode"),
        "coupon_type": coupon.get("coupon_type"),
        "value": coupon.get("value"),
        "maximum_discount": coupon.get("maximum_discount"),
        "minimum_bill": coupon.get("minimum_bill"),
        "is_active": coupon.get("is_active", True),
        "expire_date": expire_date,
        "admin_id": coupon.get("admin_id"),
    }


def all_coupons_data(coupons) -> list:
    return [coupon_data(coupon) for coupon in coupons]