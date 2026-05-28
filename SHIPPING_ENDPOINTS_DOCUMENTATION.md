# 🚚 Shipping Management API Endpoints

**Base URL:** `http://18.61.65.71:5454`

**Authentication:** Required (Admin Token in Header)  
**Header:** `Authorization: Bearer <admin_token>`

---

## 📋 Table of Contents
1. [Update Zone](#update-zone)
2. [Delete Zone](#delete-zone)
3. [Delete State](#delete-state)
4. [Delete Country](#delete-country)

---

## 🔧 Update Zone

**Endpoint:** `PATCH /shipping/admin/{admin_id}/edit-zone`

**Full URL:** `http://18.61.65.71:5454/shipping/admin/{admin_id}/edit-zone`

**Description:** Update zone pricing and free delivery threshold. Admin can update one or both fields.

### Request Headers
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

### Request Body
```json
{
  "country": "India",
  "state_name": "Telangana",
  "old_start_zipcode": 500001,
  "old_end_zipcode": 500050,
  "new_charge_per_kg": 25.0,
  "new_free_delivery_min_order_value": 1000.0
}
```

### Request Body (Optional Fields Example - Update only charge)
```json
{
  "country": "India",
  "state_name": "Telangana",
  "old_start_zipcode": 500001,
  "old_end_zipcode": 500050,
  "new_charge_per_kg": 25.0
}
```

### Response (Success - 200)
```json
{
  "message": "Zone updated successfully",
  "country": "India",
  "state": "Telangana",
  "zone_identified_by": {
    "start_zipcode": 500001,
    "end_zipcode": 500050
  },
  "previous_values": {
    "charge_per_kg": 15.0,
    "free_delivery_min_order_value": 500.0
  },
  "updated_values": {
    "charge_per_kg": 25.0,
    "free_delivery_min_order_value": 1000.0
  }
}
```

### Error Responses
- **404 - Country not found:**
```json
{
  "detail": "Country config not found"
}
```

- **404 - Zone not found:**
```json
{
  "detail": "Zone not found with those zipcode ranges"
}
```

---

## 🗑️ Delete Zone

**Endpoint:** `DELETE /shipping/admin/{admin_id}/delete-zone`

**Full URL:** `http://18.61.65.71:5454/shipping/admin/{admin_id}/delete-zone`

**Description:** Delete a specific zone from a state.

### Request Headers
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

### Request Body
```json
{
  "country": "India",
  "state_name": "Telangana",
  "start_zipcode": 500001,
  "end_zipcode": 500050
}
```

### Response (Success - 200)
```json
{
  "message": "Zone deleted successfully",
  "country": "India",
  "state": "Telangana",
  "deleted_zone": {
    "start_zipcode": 500001,
    "end_zipcode": 500050
  }
}
```

### Error Responses
- **404 - Country not found:**
```json
{
  "detail": "Country config not found"
}
```

- **404 - State not found:**
```json
{
  "detail": "State not found"
}
```

- **404 - Zone not found:**
```json
{
  "detail": "Zone not found with those zipcode ranges"
}
```

---

## 🗑️ Delete State

**Endpoint:** `DELETE /shipping/admin/{admin_id}/delete-state`

**Full URL:** `http://18.61.65.71:5454/shipping/admin/{admin_id}/delete-state`

**Description:** Delete a complete state and all its zones.

### Request Headers
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

### Request Body
```json
{
  "country": "India",
  "state_name": "Karnataka"
}
```

### Response (Success - 200)
```json
{
  "message": "State and all its zones deleted successfully",
  "country": "India",
  "deleted_state": "Karnataka"
}
```

### Error Responses
- **404 - Country not found:**
```json
{
  "detail": "Country config not found"
}
```

- **404 - State not found:**
```json
{
  "detail": "State not found"
}
```

---

## 🗑️ Delete Country

**Endpoint:** `DELETE /shipping/admin/{admin_id}/delete-country`

**Full URL:** `http://18.61.65.71:5454/shipping/admin/{admin_id}/delete-country?country=India`

**Description:** Delete a complete country configuration and all its states and zones.

### Request Headers
```
Authorization: Bearer <admin_token>
```

### Query Parameters
```
country: India  (URL parameter)
```

### Response (Success - 200)
```json
{
  "message": "Country configuration deleted successfully",
  "deleted_country": "India",
  "admin_id": "admin123",
  "states_deleted": 5
}
```

### Error Responses
- **404 - Country not found:**
```json
{
  "detail": "Country configuration not found"
}
```

---

## 📝 CURL Examples

### Update Zone
```bash
curl -X PATCH http://18.61.65.71:5454/shipping/admin/admin123/edit-zone \
  -H "Authorization: Bearer your_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "India",
    "state_name": "Telangana",
    "old_start_zipcode": 500001,
    "old_end_zipcode": 500050,
    "new_charge_per_kg": 25.0,
    "new_free_delivery_min_order_value": 1000.0
  }'
```

### Delete Zone
```bash
curl -X DELETE http://18.61.65.71:5454/shipping/admin/admin123/delete-zone \
  -H "Authorization: Bearer your_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "India",
    "state_name": "Telangana",
    "start_zipcode": 500001,
    "end_zipcode": 500050
  }'
```

### Delete State
```bash
curl -X DELETE http://18.61.65.71:5454/shipping/admin/admin123/delete-state \
  -H "Authorization: Bearer your_admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "India",
    "state_name": "Karnataka"
  }'
```

### Delete Country
```bash
curl -X DELETE "http://18.61.65.71:5454/shipping/admin/admin123/delete-country?country=India" \
  -H "Authorization: Bearer your_admin_token"
```

---

## 🔑 Required Parameters Summary

| Endpoint | Required Params | Optional Params |
|----------|-----------------|-----------------|
| Update Zone | country, state_name, old_start_zipcode, old_end_zipcode | new_charge_per_kg, new_free_delivery_min_order_value |
| Delete Zone | country, state_name, start_zipcode, end_zipcode | - |
| Delete State | country, state_name | - |
| Delete Country | country (query param) | - |

---

## ✅ Status Codes

- **200:** Success
- **400:** Bad Request (Invalid data)
- **404:** Resource Not Found
- **429:** Rate Limited
- **500:** Server Error

---

## 🔐 Authentication Note

All endpoints require admin authentication. Include the Bearer token in the Authorization header:

```
Authorization: Bearer <your_admin_token>
```

---

**Last Updated:** May 28, 2026  
**API Version:** 1.0
