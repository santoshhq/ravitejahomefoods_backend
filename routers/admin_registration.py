from config.collection import admin_registartion_collection
from config.jwt_auth.token_creation import create_access_token, get_current_admin
from models.admin_registration import (
    LoginResponse,
    Registration,
    RegistrationResponse,
    updateRegistration,
)
from schemas.admin_registration import all_data , indiviual_data
from fastapi import APIRouter, Depends, HTTPException, Request, status
from config.rate_limiter import limiter, RATE_LIMITS
from fastapi.security import OAuth2PasswordRequestForm
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument


admin_registration_router=APIRouter(prefix="/admin-registration",tags=["Admin-Authentication"])

@admin_registration_router.post("/create", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["admin_create"])
async def creater_registration(request: Request, register: Registration):
    try:
        payload = register.model_dump(mode="json")
        response = await admin_registartion_collection.insert_one(payload)
        created_user = await admin_registartion_collection.find_one({"_id": response.inserted_id})
        if not created_user:
            raise HTTPException(status_code=500, detail="Failed to fetch created user")
        return {
            "message": "Successfully Inserted",
            "data": indiviual_data(created_user),
        }
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            raise HTTPException(status_code=409, detail="Email already exists")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@admin_registration_router.post("/login", response_model=LoginResponse)
@limiter.limit(RATE_LIMITS["admin_login"])
async def admin_login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        admin = await admin_registartion_collection.find_one({"email": form_data.username})
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if admin.get("password") != form_data.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token_payload = {
            "sub": str(admin.get("_id")),
            "email": admin.get("email"),
            "fullname": admin.get("fullname"),
        }
        access_token = create_access_token(token_payload)

        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "admin": {
                "id": str(admin.get("_id")),
                "fullname": admin.get("fullname"),
                "email": admin.get("email"),
                "mobile": admin.get("mobile"),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_registration_router.post("/refresh")
@limiter.limit(RATE_LIMITS["admin_refresh"])
async def refresh_token(request: Request, _current_admin: dict = Depends(get_current_admin)):
    try:
        token_payload = {
            "sub": str(_current_admin.get("id")),
            "email": _current_admin.get("email"),
            "fullname": _current_admin.get("fullname"),
        }
        access_token = create_access_token(token_payload)

        return {
            "message": "Token refreshed successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "admin": {
                "id": str(_current_admin.get("id")),
                "fullname": _current_admin.get("fullname"),
                "email": _current_admin.get("email"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing token: {str(e)}")

    
@admin_registration_router.put("/update-registration/{user_id}", response_model=RegistrationResponse)
@admin_registration_router.put("/update-regratration/{user_id}", include_in_schema=False, response_model=RegistrationResponse)
@limiter.limit(RATE_LIMITS["admin_update"])
async def update_user(
    request: Request,
    user_id: str,
    register: updateRegistration,
    _current_admin: dict = Depends(get_current_admin),
):
    try:
        updated_data = register.model_dump(exclude_unset=True)
        if not updated_data:
            raise HTTPException(status_code=400, detail="No fields provided to update")

        updated_user = await admin_registartion_collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": updated_data},
            return_document=ReturnDocument.AFTER,
        )
        if updated_user is None:
            raise HTTPException(status_code=404, detail="Registration not found")

        return {"message": "Successfully Updated", "data": indiviual_data(updated_user)}
    except HTTPException:
        raise
    except (InvalidId, ValueError):
        raise HTTPException(status_code=400, detail="Invalid user_id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")