from bson.errors import InvalidId
from bson.objectid import ObjectId
from fastapi import APIRouter, HTTPException, status, Query
import re
from pymongo import ReturnDocument
from typing import Literal, Optional
from config.collection import categories_collection, products_collection
from models.categories_models import CreateCategory, UpdateCategory
from schemas.categories_schema import all_data, indiviual_data


categories_router = APIRouter(prefix="/categories", tags=["Categories"])


@categories_router.post("/create")
async def create_category(data: CreateCategory):
	try:
		# Check for duplicate category name (case-insensitive)
		existing = await categories_collection.find_one({"name": {"$regex": f"^{re.escape(data.name)}$", "$options": "i"}})
		if existing:
			raise HTTPException(status_code=400, detail="Category with this name already exists")

		payload = data.model_dump(mode="json")
		# Ensure admin_id is present in payload (if not, raise error)
		if not payload.get("admin_id"):
			raise HTTPException(status_code=400, detail="admin_id is required for category creation")
		response = await categories_collection.insert_one(payload)
		created_category = await categories_collection.find_one({"_id": response.inserted_id})
		if not created_category:
			raise HTTPException(status_code=500, detail="Failed to fetch created category")
		return {
			"message": "Category created successfully",
			"data": indiviual_data(created_category),
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@categories_router.get("/", status_code=status.HTTP_200_OK)
async def get_categories(admin_id: Optional[str] = None):
	"""
	Get all categories. If admin_id is provided, only return categories created by that admin.
	"""
	try:
		query = {"admin_id": admin_id} if admin_id else {}
		categories = await categories_collection.find(query).to_list(length=None)
		return {
			"count": len(categories),
			"data": all_data(categories),
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
# Get all categories for a specific admin
@categories_router.get("/by-admin/{admin_id}", status_code=status.HTTP_200_OK)
async def get_categories_by_admin(admin_id: str):
	"""
	Get all categories created by a specific admin.
	"""
	try:
		categories = await categories_collection.find({"admin_id": admin_id}).to_list(length=None)
		return {
			"count": len(categories),
			"data": all_data(categories),
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@categories_router.get("/by-name/{category_name}/subcategories")
async def get_subcategories_by_category_name(category_name: str):
	try:
		category = await categories_collection.find_one(
			{"name": {"$regex": f"^{re.escape(category_name)}$", "$options": "i"}}
		)
		if not category:
			raise HTTPException(status_code=404, detail="Category not found")

		subcategories = category.get("subcategory") or []
		subcategory_names = []
		for item in subcategories:
			if isinstance(item, dict):
				name = item.get("name")
				if name:
					subcategory_names.append(name)
			elif isinstance(item, str):
				subcategory_names.append(item)

		return {
			"category_name": category.get("name"),
			"count": len(subcategory_names),
			"subcategories": subcategory_names,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@categories_router.get("/by-business-type/{business_type}")
async def get_categories_by_business_type(
	business_type: Literal["retail", "wholesale"],
	admin_id: str = Query(..., description="Admin ID (required)")
):
	"""
	Get all categories for a business type and admin. admin_id is required.
	"""
	if not admin_id:
		raise HTTPException(status_code=400, detail="admin_id is required")
	try:
		query = {"business_type": business_type, "admin_id": admin_id}
		categories = await categories_collection.find(query).to_list(length=None)
		return {
			"business_type": business_type,
			"count": len(categories),
			"data": all_data(categories),
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@categories_router.get("/{category_id}")
async def get_category(category_id: str):
	try:
		category = await categories_collection.find_one({"_id": ObjectId(category_id)})
		if not category:
			raise HTTPException(status_code=404, detail="Category not found")
		return {"data": indiviual_data(category)}
	except (InvalidId, ValueError):
		raise HTTPException(status_code=400, detail="Invalid category_id")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@categories_router.put("/{category_id}")
async def update_category(category_id: str, data: UpdateCategory):
	try:
		updated_data = data.model_dump(mode="json", exclude_unset=True, exclude_none=True)
		if not updated_data:
			raise HTTPException(status_code=400, detail="No fields provided to update")

		updated_category = await categories_collection.find_one_and_update(
			{"_id": ObjectId(category_id)},
			{"$set": updated_data},
			return_document=ReturnDocument.AFTER,
		)
		if not updated_category:
			raise HTTPException(status_code=404, detail="Category not found")
		return {
			"message": "Category updated successfully",
			"data": indiviual_data(updated_category),
		}
	except (InvalidId, ValueError):
		raise HTTPException(status_code=400, detail="Invalid category_id")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@categories_router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: str):
	try:
		# Check if any product is linked to this category
		linked_product = await products_collection.find_one({"category_id": str(category_id)})
		if linked_product:
			raise HTTPException(status_code=400, detail="Cannot delete category: products are linked to this category.")
		deleted_result = await categories_collection.delete_one({"_id": ObjectId(category_id)})
		if deleted_result.deleted_count == 0:
			raise HTTPException(status_code=404, detail="Category not found")
		return {"message": "Category deleted successfully"}
	except (InvalidId, ValueError):
		raise HTTPException(status_code=400, detail="Invalid category_id")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
