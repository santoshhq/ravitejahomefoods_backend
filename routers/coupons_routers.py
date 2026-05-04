from fastapi import APIRouter, HTTPException, Request, status, Form, Query
from config.collection import coupons_collection
from models.coupons_models import CreateCoupon, UpdateCoupon
from schemas.coupons_schema import coupon_data, all_coupons_data
from typing import Optional, Literal
from bson import ObjectId
from config.rate_limiter import limiter, RATE_LIMITS

coupon_router = APIRouter(prefix="/coupons", tags=["Coupons"])


# --- Helper ---
def get_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


# --- Create Coupon ---
@coupon_router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    name="coupons:create-coupon",
    summary="Create a new coupon",
)
@limiter.limit(RATE_LIMITS["coupon_write"])
async def create_coupon(
    request: Request,
    couponcode: str = Form(...),
    coupon_type: Literal["percentage", "fixed"] = Form(...),
    value: float = Form(...),
    maximum_discount: Optional[float] = Form(None),
    minimum_bill: Optional[float] = Form(None),
    is_active: bool = Form(True),
    expire_date: Optional[str] = Form(None),
    admin_id: str = Form(...),
):
    normalized_code = couponcode.strip().lower()

    existing = await coupons_collection.find_one({"couponcode": normalized_code})
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")

    data = {
        "couponcode": normalized_code,
        "coupon_type": coupon_type,
        "value": value,
        "maximum_discount": maximum_discount,
        "minimum_bill": minimum_bill,
        "is_active": is_active,
        "expire_date": expire_date,
        "admin_id": admin_id,
    }

    coupon = CreateCoupon(**data)
    coupon_dict = coupon.model_dump()
    result = await coupons_collection.insert_one(coupon_dict.copy())
    coupon_dict["_id"] = result.inserted_id

    return {"message": "Coupon created", "data": coupon_data(coupon_dict)}


# --- Get All Coupons by Admin ---
@coupon_router.get(
    "/by-admin",
    response_model=dict,
    name="coupons:get-coupons-by-admin",
    summary="Get all coupons by admin ID",
)
@limiter.limit(RATE_LIMITS["coupon_read"])
async def get_coupons_by_admin(request: Request, admin_id: str = Query(...)):
    coupons = await coupons_collection.find({"admin_id": admin_id}).to_list(length=None)
    return {"data": all_coupons_data(coupons)}


# --- Get Single Coupon ---
@coupon_router.get(
    "/{coupon_id}",
    response_model=dict,
    name="coupons:get-coupon",
    summary="Get a single coupon by ID",
)
@limiter.limit(RATE_LIMITS["coupon_read"])
async def get_coupon(request: Request, coupon_id: str):
    coupon = await coupons_collection.find_one({"_id": get_object_id(coupon_id)})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return {"data": coupon_data(coupon)}


# --- Update Coupon ---
@coupon_router.put(
    "/{coupon_id}",
    response_model=dict,
    name="coupons:update-coupon",
    summary="Update a coupon by ID",
)
@limiter.limit(RATE_LIMITS["coupon_write"])
async def update_coupon(
    request: Request,
    coupon_id: str,
    couponcode: Optional[str] = Form(None),
    coupon_type: Optional[Literal["percentage", "fixed"]] = Form(None),
    value: Optional[float] = Form(None),
    maximum_discount: Optional[float] = Form(None),
    minimum_bill: Optional[float] = Form(None),
    is_active: Optional[bool] = Form(None),
    expire_date: Optional[str] = Form(None),
    admin_id: Optional[str] = Form(None),
):
    object_id = get_object_id(coupon_id)

    raw_update = {
        "couponcode": couponcode.strip().lower() if couponcode else None,
        "coupon_type": coupon_type,
        "value": value,
        "maximum_discount": maximum_discount,
        "minimum_bill": minimum_bill,
        "is_active": is_active,
        "expire_date": expire_date,
        "admin_id": admin_id,
    }

    update_data = {k: v for k, v in raw_update.items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided to update")

    UpdateCoupon(**update_data)

    result = await coupons_collection.update_one(
        {"_id": object_id}, {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Coupon not found")
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes were made (values may be the same)")

    updated_coupon = await coupons_collection.find_one({"_id": object_id})
    return {"message": "Coupon updated", "data": coupon_data(updated_coupon)}


# --- Delete Coupon ---
@coupon_router.delete(
    "/{coupon_id}",
    response_model=dict,
    name="coupons:delete-coupon",
    summary="Delete a coupon by ID",
)
@limiter.limit(RATE_LIMITS["coupon_write"])
async def delete_coupon(
    request: Request,
    coupon_id: str,
    admin_id: str = Query(..., description="Admin ID for authorization"),
):
    object_id = get_object_id(coupon_id)

    coupon = await coupons_collection.find_one({"_id": object_id})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    if coupon.get("admin_id") != admin_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this coupon")

    await coupons_collection.delete_one({"_id": object_id})
    return {"message": "Coupon deleted successfully"}