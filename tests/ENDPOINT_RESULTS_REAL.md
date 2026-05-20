# Endpoint Results (Real Services)

This suite uses real MongoDB, Redis, S3, and Razorpay. Resend is disabled in tests to avoid live email.

## Notes
- Database used: RaviTejaFoods_test (set via DB_NAME env var)
- Razorpay verify-payment requires a real payment signature; test is skipped unless LIVE_RAZORPAY_* env vars are set.
- S3 uploads are real; tests delete uploaded objects.

## Razorpay manual verify-payment
Set these env vars after a real payment completes:
- LIVE_RAZORPAY_ORDER_ID
- LIVE_RAZORPAY_PAYMENT_ID
- LIVE_RAZORPAY_SIGNATURE

Then run:
- pytest tests/integration/test_orders_real.py -k verify

## Clear results per endpoint
Use the unit test samples in tests/ENDPOINT_RESULTS.md as baseline, and this file for live notes.

## Reviews

| Method | Path | Expected Status | Sample Response |
| --- | --- | --- | --- |
| POST | /reviews/create_review | 201 | {"message": "Review created", "data": {"id": "..."}} |
| GET | /reviews/product/{product_id} | 200 | {"count": 1, "avg_rating": 5.0, "data": [{"id": "...", "rating": 5}]} |
| GET | /reviews/{review_id} | 200 | {"data": {"id": "...", "review_title": "Great"}} |
| PUT | /reviews/update_review/{review_id} | 200 | {"message": "Review updated", "data": {"id": "..."}} |
| DELETE | /reviews/delete_review/{review_id} | 200 | {"message": "Review deleted", "data": {"id": "..."}} |
| DELETE | /reviews/delete_by_product/{product_id} | 200 | {"message": "Reviews deleted", "deleted_count": 1, "product_id": "..."} |
