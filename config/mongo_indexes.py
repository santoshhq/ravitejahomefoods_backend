from pymongo import ASCENDING, DESCENDING
from config.collection import (
    admin_registartion_collection,
    categories_collection,
    products_collection,
    coupons_collection,
    users_collection,
    carts_collection,
    orders_collection,
    shipping_charges,
)


async def create_indexes() -> None:
    await admin_registartion_collection.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="uniq_admin_email",
    )

    await categories_collection.create_index(
        [("admin_id", ASCENDING)],
        name="categories_admin_id",
    )
    await categories_collection.create_index(
        [("business_type", ASCENDING), ("admin_id", ASCENDING)],
        name="categories_business_admin",
    )
    await categories_collection.create_index(
        [("name", ASCENDING)],
        name="categories_name",
    )

    await products_collection.create_index(
        [("admin_id", ASCENDING)],
        name="products_admin_id",
    )
    await products_collection.create_index(
        [("category_id", ASCENDING)],
        name="products_category_id",
    )
    await products_collection.create_index(
        [("is_active", ASCENDING)],
        name="products_is_active",
    )
    await products_collection.create_index(
        [("category_id", ASCENDING), ("subcategory", ASCENDING), ("is_active", ASCENDING)],
        name="products_category_subcategory_active",
    )

    await coupons_collection.create_index(
        [("couponcode", ASCENDING)],
        unique=True,
        name="coupons_code_unique",
    )
    await coupons_collection.create_index(
        [("admin_id", ASCENDING)],
        name="coupons_admin_id",
    )

    await users_collection.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="users_email_unique",
    )

    await carts_collection.create_index(
        [("user_email", ASCENDING)],
        unique=True,
        sparse=True,
        name="carts_user_email_unique",
    )
    await carts_collection.create_index(
        [("guest_id", ASCENDING)],
        unique=True,
        sparse=True,
        name="carts_guest_id_unique",
    )
    await carts_collection.create_index(
        [("items.product_id", ASCENDING), ("items.weight", ASCENDING)],
        name="carts_items_product_weight",
    )

    await orders_collection.create_index(
        [("guest_id", ASCENDING), ("created_at", DESCENDING)],
        name="orders_guest_created_at",
    )
    await orders_collection.create_index(
        [("created_at", DESCENDING)],
        name="orders_created_at",
    )

    await shipping_charges.create_index(
        [("country", ASCENDING)],
        name="shipping_country",
    )
    await shipping_charges.create_index(
        [("admin_id", ASCENDING), ("country", ASCENDING)],
        unique=True,
        name="shipping_admin_country_unique",
    )
