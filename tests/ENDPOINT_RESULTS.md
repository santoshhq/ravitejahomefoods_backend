# Endpoint Results (Sample)

These samples reflect the unit test responses using mocked services and in-memory collections.

## Health

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| GET | / | 200 | {"message": "Raviteja Foods Backend is running"} |

## Admin Registration

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /admin-registration/create | 201 | {"message": "Successfully Inserted", "data": {"id": "...", "fullname": "Admin Two", "email": "admin2@example.com", "mobile": "8888888888"}} |
| POST | /admin-registration/login | 200 | {"message": "Login successful", "access_token": "testtoken", "token_type": "bearer", "admin": {"id": "...", "fullname": "Admin One", "email": "admin@example.com", "mobile": "9999999999"}} |
| POST | /admin-registration/refresh | 200 | {"message": "Token refreshed successfully", "access_token": "testtoken", "token_type": "bearer", "admin": {"id": "...", "fullname": "Admin One", "email": "admin@example.com"}} |
| PUT | /admin-registration/update-registration/{user_id} | 200 | {"message": "Successfully Updated", "data": {"id": "...", "fullname": "Admin Updated", "email": "admin@example.com", "mobile": "9999999999"}} |

## Categories

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /categories/create | 200 | {"message": "Category created successfully", "data": {"id": "...", "name": "Beverages"}} |
| GET | /categories/ | 200 | {"count": 2, "data": [{"id": "...", "name": "Snacks"}]} |
| GET | /categories/by-admin/{admin_id} | 200 | {"count": 1, "data": [{"id": "...", "name": "Snacks"}]} |
| GET | /categories/by-name/{category_name}/subcategories | 200 | {"category_name": "Snacks", "count": 2, "subcategories": ["Chips", "Mix"]} |
| GET | /categories/by-business-type/{business_type}?admin_id=... | 200 | {"business_type": "retail", "count": 1, "data": [{"id": "...", "name": "Snacks"}]} |
| GET | /categories/{category_id} | 200 | {"data": {"id": "...", "name": "Snacks"}} |
| PUT | /categories/{category_id} | 200 | {"message": "Category updated successfully", "data": {"id": "...", "name": "Snacks Updated"}} |
| DELETE | /categories/{category_id} | 200 | {"message": "Category deleted successfully"} |
| GET | /categories/all_Categories/{business_type} | 200 | {"count": 1, "data": [{"id": "...", "name": "Snacks"}]} |

## Products

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /products/create_product | 200 | {"message": "Successfully Inserted", "product_id": "...", "images_url": ["https://example.com/p.png"]} |
| GET | /products/all | 200 | {"count": 1, "data": [{"id": "...", "product_name": "Masala Chips"}]} |
| GET | /products/get_active_products | 200 | {"count": 1, "data": [{"id": "...", "product_name": "Masala Chips"}]} |
| GET | /products/active-by-category?category_id=... | 200 | {"count": 1, "data": [{"id": "...", "product_name": "Masala Chips"}]} |
| GET | /products/by-admin/{admin_id} | 200 | {"count": 1, "data": [{"id": "...", "product_name": "Masala Chips"}]} |
| GET | /products/get_product/{product_id} | 200 | {"id": "...", "product_name": "Masala Chips", "reviews": []} |
| PUT | /products/update_product/{product_id} | 200 | {"message": "Product updated", "updated_fields": {"description": "Updated"}} |
| DELETE | /products/delete_product/{product_id} | 200 | {"message": "Product deleted and images removed from S3"} |
| GET | /products/business_type_products/{business_type} | 200 | {"count": 1, "data": [{"id": "...", "product_name": "Masala Chips"}]} |

## Uploads

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /imagesuploads/images | 200 | {"image_urls": ["https://weetshop-images.s3.us-east-1.amazonaws.com/products/..."]} |
| POST | /imagesuploads/get_images | 200 | {"image_urls": ["https://example.com/x.png"]} |
| GET | /imagesuploads/all_images | 200 | {"image_urls": []} |
| PUT | /imagesuploads/update_images | 200 | {"image_urls": []} |
| DELETE | /imagesuploads/delete_images | 200 | {"deleted": ["https://example.com/x.png"], "errors": []} |

## Coupons

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /coupons/ | 201 | {"message": "Coupon created", "data": {"id": "...", "couponcode": "save20"}} |
| GET | /coupons/by-admin?admin_id=... | 200 | {"data": [{"id": "...", "couponcode": "save20"}]} |
| GET | /coupons/{coupon_id} | 200 | {"data": {"id": "...", "couponcode": "save10"}} |
| PUT | /coupons/{coupon_id} | 200 | {"message": "Coupon updated", "data": {"id": "...", "couponcode": "save10"}} |
| DELETE | /coupons/{coupon_id}?admin_id=... | 200 | {"message": "Coupon deleted successfully"} |

## User Login

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /user-login/request-otp | 200 | {"message": "OTP sent to email"} |
| POST | /user-login/verify-otp | 200 | {"access_token": "testtoken", "token_type": "bearer"} |
| GET | /user-login/me | 200 | {"id": "...", "email": "user@example.com"} |

## Cart

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| GET | /cart?guest_id=... | 200 | {"data": {"items": []}} |
| POST | /cart/add-bulk | 200 | {"message": "1 item(s) processed", "data": {"items": [{"product_id": "prod-1"}]}} |
| PUT | /cart/update | 200 | {"message": "Cart updated", "data": {"items": [{"product_id": "prod-1", "quantity": 2}]}} |
| DELETE | /cart/clear?guest_id=... | 200 | {"message": "Cart cleared successfully"} |
| POST | /cart/apply-coupon | 200 | {"message": "Coupon applied! You save Rs10", "data": {"coupon_code": "save10"}} |
| DELETE | /cart/remove-coupon?guest_id=... | 200 | {"message": "Coupon removed", "data": {"coupon_code": null}} |
| POST | /cart/merge | 200 | {"message": "Guest cart merged into your account successfully", "data": {"items": []}} |

## Orders

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /orders/delivery-estimate | 200 | {"shipping_charge": 0.0, "free_delivery": true} |
| POST | /orders/place | 201 | {"status": "success", "razorpay_order_id": "order_test_1", "grand_total": 100.0} |
| POST | /orders/verify-payment | 200 | {"status": "success", "order_id": "...", "custom_order_id": "ORD2026ABC1234"} |
| GET | /orders/guest/{guest_id} | 200 | {"data": [{"id": "...", "order_status": "confirmed"}]} |
| GET | /orders/admin/all-orders | 200 | {"message": "All orders fetched successfully", "count": 1, "data": []} |

## Shipping

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /shipping/admin/{admin_id}/rules | 200 | {"message": "Shipping rules created", "data": {"id": "...", "country": "India"}} |
| GET | /shipping/admin/{admin_id}/rules | 200 | {"count": 1, "data": [{"country": "India"}]} |
| GET | /shipping/countries | 200 | {"countries": ["India"]} |
| GET | /shipping/countries/{country}/states | 200 | {"country": "India", "states": ["Telangana"]} |
| POST | /shipping/admin/{admin_id}/add-state | 200 | {"message": "State added successfully"} |
| POST | /shipping/admin/{admin_id}/add-zone | 200 | {"message": "Zone added successfully"} |
| POST | /shipping/estimate | 200 | {"shipping_charge": 10.0, "free_delivery": false} |

## Reviews

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /reviews/create_review | 201 | {"message": "Review created", "data": {"id": "..."}} |
| GET | /reviews/product/{product_id} | 200 | {"count": 1, "avg_rating": 5.0, "data": [{"id": "...", "rating": 5}]} |
| GET | /reviews/{review_id} | 200 | {"data": {"id": "...", "review_title": "Great"}} |
| PUT | /reviews/update_review/{review_id} | 200 | {"message": "Review updated", "data": {"id": "..."}} |
| DELETE | /reviews/delete_review/{review_id} | 200 | {"message": "Review deleted", "data": {"id": "..."}} |
| DELETE | /reviews/delete_by_product/{product_id} | 200 | {"message": "Reviews deleted", "deleted_count": 1, "product_id": "..."} |

## Dashboard

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| GET | /dashboard/overview | 200 | {"total": {"sales": 0, "revenue": 0.0}, "daily": {"sales": 0, "revenue": 0.0}} |
