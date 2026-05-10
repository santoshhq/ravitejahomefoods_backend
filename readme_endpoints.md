# RaviTeja Foods API Endpoints

Base URL: http://18.61.65.71:5454/

## Authentication
- Admin endpoints use Bearer token from /admin-registration/login.
- User endpoints use Bearer token from /user-login/verify-otp (JWT).
- Cart endpoints support guest flow via guest_id when no token is available.

## Admin Authentication (adminCredentials)
### POST /admin-registration/create
Creates a new admin account.

Request (JSON)
```json
{
  "fullname": "Admin One",
  "mobile": "9876543210",
  "email": "admin@example.com",
  "password": "StrongPass123"
}
```

Response 201
```json
{
  "message": "Successfully Inserted",
  "data": {
    "id": "65f1b8f2f3a0c12a1a0b0001",
    "fullname": "Admin One",
    "email": "admin@example.com",
    "mobile": "9876543210"
  }
}
```

### POST /admin-registration/login
Logs in admin and returns access token.

Request (form-urlencoded)
- username: admin email
- password: admin password

Response 200
```json
{
  "message": "Login successful",
  "access_token": "<jwt>",
  "token_type": "bearer",
  "admin": {
    "id": "65f1b8f2f3a0c12a1a0b0001",
    "fullname": "Admin One",
    "email": "admin@example.com",
    "mobile": "9876543210"
  }
}
```

### POST /admin-registration/refresh
Refreshes admin token (requires Bearer token).

Response 200
```json
{
  "message": "Token refreshed successfully",
  "access_token": "<jwt>",
  "token_type": "bearer",
  "admin": {
    "id": "65f1b8f2f3a0c12a1a0b0001",
    "fullname": "Admin One",
    "email": "admin@example.com"
  }
}
```

### PUT /admin-registration/update-registration/{user_id}
Updates admin profile (requires Bearer token).

Request (JSON)
```json
{
  "fullname": "Admin One Updated",
  "mobile": "9876543210"
}
```

Response 200
```json
{
  "message": "Successfully Updated",
  "data": {
    "id": "65f1b8f2f3a0c12a1a0b0001",
    "fullname": "Admin One Updated",
    "email": "admin@example.com",
    "mobile": "9876543210"
  }
}
```

## User Login (users)
### POST /user-login/request-otp
Sends OTP to email for login.

Request (query)
- email: user email

Response 200
```json
{ "message": "OTP sent to email" }
```

### POST /user-login/verify-otp
Verifies OTP and returns JWT.

Request (query)
- email: user email
- otp: 6-digit OTP

Response 200
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### GET /user-login/me
Returns logged-in user details (requires Bearer token).

Response 200
```json
{
  "id": "65f1c2c1f3a0c12a1a0b0002",
  "email": "user@example.com",
  "is_verified": true,
  "last_login": "2026-05-10T10:15:20.000Z"
}
```

## Categories (categories)
### POST /categories/create
Creates a category.

Request (JSON)
```json
{
  "name": "Spices",
  "business_type": "retail",
  "subcategory": [{"name": "Whole"}, {"name": "Powder"}],
  "admin_id": "65f1b8f2f3a0c12a1a0b0001"
}
```

Response 200
```json
{
  "message": "Category created successfully",
  "data": {
    "id": "65f1cc11f3a0c12a1a0b0003",
    "name": "Spices",
    "business_type": "retail",
    "subcategory": [{"name": "Whole"}, {"name": "Powder"}],
    "admin_id": "65f1b8f2f3a0c12a1a0b0001"
  }
}
```

### GET /categories/
Returns all categories (optional admin_id filter).

Query
- admin_id: optional

Response 200
```json
{
  "count": 1,
  "data": [
    {
      "id": "65f1cc11f3a0c12a1a0b0003",
      "name": "Spices",
      "business_type": "retail",
      "subcategory": [{"name": "Whole"}],
      "admin_id": "65f1b8f2f3a0c12a1a0b0001"
    }
  ]
}
```

### GET /categories/by-admin/{admin_id}
Returns categories for a specific admin.

### GET /categories/by-name/{category_name}/subcategories
Returns subcategory names for a category.

Response 200
```json
{
  "category_name": "Spices",
  "count": 2,
  "subcategories": ["Whole", "Powder"]
}
```

### GET /categories/by-business-type/{business_type}
Returns categories by business type and admin.

Query
- admin_id: required

### GET /categories/{category_id}
Returns a single category by ID.

### PUT /categories/{category_id}
Updates category fields.

Request (JSON)
```json
{
  "name": "Spices and Herbs",
  "subcategory": [{"name": "Herbs"}]
}
```

### DELETE /categories/{category_id}
Deletes category (blocked if products are linked).

### GET /categories/all_Categories/{business_type}
Returns only category names for given business type.

Response 200
```json
["Spices", "Dry Fruits", "Snacks"]
```

## Products (products)
### POST /products/create_product
Creates a product. Uses multipart/form-data.

Request (form-data)
- product_name: string
- description: string
- business_type: retail | wholesale
- category_id: string
- subcategory: optional string
- pricing: JSON string (list of {"weight","price","stock"})
- is_active: true|false
- image_urls: JSON string (list of S3 URLs)
- admin_id: string

Response 200
```json
{
  "message": "Successfully Inserted",
  "product_id": "65f1d041f3a0c12a1a0b0004",
  "images_url": ["https://bucket.s3.amazonaws.com/products/abc.jpg"]
}
```

### GET /products/all
Returns all products (optional admin_id filter).

### GET /products/get_active_products
Returns all active products.

### GET /products/active-by-category
Returns active products by category_id and optional subcategory.

Query
- category_id: required
- subcategory: optional

### GET /products/by-admin/{admin_id}
Returns products for an admin.

### GET /products/get_product/{product_id}
Returns a product with its active reviews.

Response 200
```json
{
  "id": "65f1d041f3a0c12a1a0b0004",
  "product_name": "Red Chilli Powder",
  "description": "Premium quality",
  "images_url": ["https://bucket.s3.amazonaws.com/products/abc.jpg"],
  "business_type": "retail",
  "category_id": "65f1cc11f3a0c12a1a0b0003",
  "subcategory": "Powder",
  "pricing": [{"weight": "500g", "price": 150, "stock": 100}],
  "is_active": true,
  "admin_id": "65f1b8f2f3a0c12a1a0b0001",
  "reviews": [
    {
      "id": "65f1e101f3a0c12a1a0b0005",
      "product_id": "65f1d041f3a0c12a1a0b0004",
      "rating": 5,
      "review_title": "Great",
      "review_content": "Nice aroma",
      "review_images_url": [],
      "display_name": "Asha",
      "email_address": "asha@example.com",
      "mobile_number": "9999999999",
      "is_active": true,
      "created_at": "2026-05-10T10:00:00.000Z",
      "updated_at": null
    }
  ]
}
```

### PUT /products/update_product/{product_id}
Updates product fields (multipart/form-data).

Request (form-data)
- product_name, description, business_type, category_id, subcategory, is_active
- pricing: JSON string
- image_urls: JSON string (list of S3 URLs)

Response 200
```json
{
  "message": "Product updated",
  "updated_fields": {
    "is_active": false
  }
}
```

### DELETE /products/delete_product/{product_id}
Deletes product and all related images.

Response 200
```json
{ "message": "Product deleted and images removed from S3" }
```

### GET /products/business_type_products/{business_type}
Returns products by business type.

## Coupons (coupons)
### POST /coupons/
Creates a coupon (multipart/form-data).

Request (form-data)
- couponcode
- coupon_type: percentage | fixed
- value
- maximum_discount (required for percentage)
- minimum_bill (optional)
- is_active (optional)
- expire_date (optional, YYYY-MM-DD)
- admin_id

Response 201
```json
{
  "message": "Coupon created",
  "data": {
    "id": "65f1e801f3a0c12a1a0b0006",
    "couponcode": "summer10",
    "coupon_type": "percentage",
    "value": 10,
    "maximum_discount": 100,
    "minimum_bill": 500,
    "is_active": true,
    "expire_date": "2026-12-31",
    "admin_id": "65f1b8f2f3a0c12a1a0b0001"
  }
}
```

### GET /coupons/by-admin
Returns coupons by admin_id.

Query
- admin_id: required

### GET /coupons/{coupon_id}
Returns a coupon.

### PUT /coupons/{coupon_id}
Updates coupon fields (multipart/form-data).

### DELETE /coupons/{coupon_id}
Deletes a coupon (requires admin_id query for authorization).

Query
- admin_id: required

## Cart (carts)
### GET /cart/
Returns current cart for logged-in user or guest.

Query
- guest_id: optional (required if no Bearer token)

Response 200
```json
{
  "data": {
    "id": "65f1f1a1f3a0c12a1a0b0007",
    "user_email": "user@example.com",
    "guest_id": null,
    "items": [
      {
        "product_id": "65f1d041f3a0c12a1a0b0004",
        "product_name": "Red Chilli Powder",
        "image_url": "https://bucket.s3.amazonaws.com/products/abc.jpg",
        "weight": "500g",
        "price": 150,
        "quantity": 2,
        "business_type": "retail",
        "line_total": 300
      }
    ],
    "item_count": 1,
    "subtotal": 300,
    "coupon_code": null,
    "discount_amount": 0,
    "total_preview": 300,
    "shipping_address": null,
    "billing_address": null,
    "updated_at": "2026-05-10T10:00:00.000Z",
    "created_at": "2026-05-10T09:00:00.000Z"
  }
}
```

### POST /cart/add-bulk
Adds multiple items to cart (guest or logged-in).

Request (JSON)
```json
{
  "guest_id": "guest-uuid-123",
  "items": [
    {
      "product_id": "65f1d041f3a0c12a1a0b0004",
      "product_name": "Red Chilli Powder",
      "image_url": "https://bucket.s3.amazonaws.com/products/abc.jpg",
      "weight": "500g",
      "price": 150,
      "quantity": 2,
      "business_type": "retail"
    }
  ]
}
```

Response 200
```json
{
  "message": "1 item(s) processed",
  "summary": ["Red Chilli Powder (500g) — added"],
  "data": { "id": "65f1f1a1f3a0c12a1a0b0007", "items": [] }
}
```

### PUT /cart/update
Updates quantity of a cart item. Set quantity=0 to remove.

Request (JSON)
```json
{
  "guest_id": "guest-uuid-123",
  "product_id": "65f1d041f3a0c12a1a0b0004",
  "weight": "500g",
  "quantity": 1
}
```

### DELETE /cart/clear
Clears entire cart.

Query
- guest_id: optional (required if no Bearer token)

### POST /cart/apply-coupon
Applies coupon code to cart and returns preview.

Request (JSON)
```json
{ "coupon_code": "summer10", "guest_id": "guest-uuid-123" }
```

Response 200
```json
{
  "message": "Coupon applied! You save ₹30",
  "data": { "id": "65f1f1a1f3a0c12a1a0b0007", "discount_amount": 30 }
}
```

### DELETE /cart/remove-coupon
Removes coupon from cart.

Query
- guest_id: optional

### POST /cart/merge
Merges guest cart into logged-in user cart (requires Bearer token).

Request (JSON)
```json
{ "guest_id": "guest-uuid-123" }
```

## Orders (orders)
### POST /orders/delivery-estimate
Estimates delivery charges based on cart and address (guest or logged-in).

Request (JSON)
```json
{
  "country": "India",
  "state": "Telangana",
  "pincode": "500081",
  "guest_id": "guest-uuid-123"
}
```

Response 200
```json
{
  "country": "India",
  "state": "Telangana",
  "pincode": "500081",
  "order_total": 300,
  "actual_weight_kg": 1,
  "billable_weight_kg": 1,
  "charge_per_kg": 30,
  "shipping_charge": 30,
  "free_delivery": false
}
```

### POST /orders/place
Creates Razorpay order and returns payment details (does not save order yet).

Request (JSON)
```json
{
  "email": "user@example.com",
  "shipping_address": {
    "name": "Asha",
    "mobile": "9999999999",
    "address_line": "H No 1-2-3",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "pincode": "500081"
  },
  "billing_address": null,
  "coupon_code": null,
  "guest_id": "guest-uuid-123"
}
```

Response 201
```json
{
  "status": "success",
  "razorpay_order_id": "order_KJd8n...",
  "razorpay_key": "rzp_test_...",
  "grand_total": 330,
  "delivery_charges": 30,
  "cart": { "id": "65f1f1a1f3a0c12a1a0b0007", "items": [] },
  "shipping_address": { "name": "Asha", "mobile": "9999999999", "address_line": "H No 1-2-3", "city": "Hyderabad", "state": "Telangana", "country": "India", "pincode": "500081" },
  "billing_address": { "name": "Asha", "mobile": "9999999999", "address_line": "H No 1-2-3", "city": "Hyderabad", "state": "Telangana", "country": "India", "pincode": "500081" },
  "email": "user@example.com"
}
```

### POST /orders/verify-payment
Verifies Razorpay payment, creates order, clears cart.

Request (JSON)
```json
{
  "razorpay_order_id": "order_KJd8n...",
  "razorpay_payment_id": "pay_KJd8n...",
  "razorpay_signature": "signature...",
  "guest_id": "guest-uuid-123"
}
```

Response 200
```json
{
  "status": "success",
  "message": "Order confirmed and cart cleared",
  "order_id": "65f20111f3a0c12a1a0b0008",
  "custom_order_id": "ORD2026ABC1234"
}
```

### GET /orders/guest/{guest_id}
Returns orders placed by a guest.

Response 200
```json
{ "data": [ { "id": "65f20111f3a0c12a1a0b0008", "grand_total": 330 } ] }
```

### GET /orders/admin/all-orders
Returns all orders for admin (requires admin Bearer token).

Query
- adminid: optional
- limit: optional (default 20)
- skip: optional (default 0)

Response 200
```json
{
  "message": "All orders fetched successfully",
  "count": 120,
  "skip": 0,
  "limit": 20,
  "data": [
    {
      "id": "65f20111f3a0c12a1a0b0008",
      "user_email": "user@example.com",
      "items": [],
      "shipping_address": { "name": "Asha", "mobile": "9999999999", "address_line": "H No 1-2-3", "city": "Hyderabad", "country": "India", "pincode": "500081" },
      "billing_address": { "name": "Asha", "mobile": "9999999999", "address_line": "H No 1-2-3", "city": "Hyderabad", "country": "India", "pincode": "500081" },
      "subtotal": 300,
      "coupon_code": null,
      "discount_amount": 0,
      "gst_amount": 0,
      "delivery_charges": 30,
      "grand_total": 330,
      "razorpay_order_id": "order_KJd8n...",
      "order_status": "confirmed",
      "payment_status": "paid",
      "created_at": "2026-05-10T10:30:00.000Z"
    }
  ]
}
```

## Reviews (reviews)
### POST /reviews/create_review
Creates a review (multipart/form-data, optional images).

Request (form-data)
- product_id
- rating (1-5 recommended)
- review_title
- review_content
- display_name
- email_address
- mobile_number
- is_active (optional)
- files (optional, multiple)

Response 200
```json
{ "message": "Review created", "review_id": "65f1e101f3a0c12a1a0b0005" }
```

### GET /reviews/product/{product_id}
Returns reviews for a product.

Query
- is_active: optional (default true)

Response 200
```json
[
  {
    "id": "65f1e101f3a0c12a1a0b0005",
    "product_id": "65f1d041f3a0c12a1a0b0004",
    "rating": 5,
    "review_title": "Great",
    "review_content": "Nice aroma",
    "review_images_url": [],
    "display_name": "Asha",
    "email_address": "asha@example.com",
    "mobile_number": "9999999999",
    "is_active": true,
    "created_at": "2026-05-10T10:00:00.000Z",
    "updated_at": null
  }
]
```

### GET /reviews/{review_id}
Returns a single review.

### PUT /reviews/update_review/{review_id}
Updates review fields (multipart/form-data).

### DELETE /reviews/delete_review/{review_id}
Deletes a review and its images.

### DELETE /reviews/delete_by_product/{product_id}
Deletes all reviews for a product.

## Shipping (shippingCharges)
### POST /shipping/admin/{admin_id}/rules
Creates shipping rules for a country.

Request (JSON)
```json
{
  "country": "India",
  "states": [
    {
      "state_name": "Telangana",
      "zones": [
        {
          "start_zipcode": 500001,
          "end_zipcode": 500100,
          "charge_per_kg": 30,
          "free_delivery_min_order_value": 500
        }
      ]
    }
  ]
}
```

Response 200
```json
{
  "message": "Shipping rules created",
  "data": {
    "id": "65f21011f3a0c12a1a0b0009",
    "admin_id": "65f1b8f2f3a0c12a1a0b0001",
    "country": "India",
    "states": []
  }
}
```

### GET /shipping/admin/{admin_id}/rules
Returns shipping rules for an admin.

### GET /shipping/countries
Returns available countries.

Response 200
```json
{ "countries": ["India"] }
```

### GET /shipping/countries/{country}/states
Returns available states for a country.

Response 200
```json
{ "country": "India", "states": ["Telangana"] }
```

### POST /shipping/admin/{admin_id}/add-state
Adds a state under a country.

Request (JSON)
```json
{
  "country": "India",
  "state": {
    "state_name": "Karnataka",
    "zones": [
      {"start_zipcode": 560001, "end_zipcode": 560100, "charge_per_kg": 30, "free_delivery_min_order_value": 500}
    ]
  }
}
```

### POST /shipping/admin/{admin_id}/add-zone
Adds a zone to an existing state.

Request (JSON)
```json
{
  "country": "India",
  "state_name": "Telangana",
  "zone": {
    "start_zipcode": 500101,
    "end_zipcode": 500200,
    "charge_per_kg": 40,
    "free_delivery_min_order_value": 700
  }
}
```

### POST /shipping/estimate
Estimates shipping for any country/state/zipcode.

Request (JSON)
```json
{
  "country": "India",
  "state": "Telangana",
  "zipcode": 500081,
  "cart_weight_grams": 1200,
  "order_total": 300
}
```

Response 200
```json
{
  "country": "India",
  "state": "Telangana",
  "zipcode": 500081,
  "actual_weight_kg": 1.2,
  "billable_weight_kg": 2,
  "charge_per_kg": 30,
  "shipping_charge": 60,
  "free_delivery": false
}
```

## Dashboard (orders)
### GET /dashboard/overview
Returns sales overview and top products.

Response 200
```json
{
  "as_of": "2026-05-10T10:45:00.000+00:00",
  "total": {"sales": 120, "revenue": 45000},
  "daily": {"sales": 5, "revenue": 1500},
  "weekly": {"sales": 30, "revenue": 12000},
  "monthly": {"sales": 80, "revenue": 30000},
  "top_products": [
    {"product_id": "65f1d041f3a0c12a1a0b0004", "product_name": "Red Chilli Powder", "units_sold": 20, "revenue": 3000}
  ]
}
```

## Image Uploads (products/reviews support)
### POST /imagesuploads/images
Uploads images to S3 (multipart/form-data).

Request (form-data)
- files: one or more files

Response 200
```json
{ "image_urls": ["https://bucket.s3.amazonaws.com/products/abc.jpg"] }
```

### POST /imagesuploads/get_images
Returns image URLs as-is.

Request (JSON)
```json
["https://bucket.s3.amazonaws.com/products/abc.jpg"]
```

Response 200
```json
{ "image_urls": ["https://bucket.s3.amazonaws.com/products/abc.jpg"] }
```

### GET /imagesuploads/all_images
Returns all product image URLs from S3.

### PUT /imagesuploads/update_images
Replaces old images and uploads new ones.

Request (form-data)
- old_image_urls: list
- files: optional list

### DELETE /imagesuploads/delete_images
Deletes images by URL.

Request (JSON)
```json
["https://bucket.s3.amazonaws.com/products/abc.jpg"]
```

Response 200
```json
{ "deleted": ["https://bucket.s3.amazonaws.com/products/abc.jpg"], "errors": [] }
```
