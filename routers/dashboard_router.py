from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

from config.collection import orders_collection
from config.rate_limiter import limiter, RATE_LIMITS


dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


SALES_FILTER = {
    "payment_status": "paid",
}


def _to_utc_naive(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


async def _aggregate_sales(query: dict) -> dict:
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": None,
                "sales_count": {"$sum": 1},
                "revenue": {"$sum": "$grand_total"},
            }
        },
    ]
    data = await orders_collection.aggregate(pipeline).to_list(1)
    if not data:
        return {"sales": 0, "revenue": 0.0}
    revenue = float(data[0].get("revenue") or 0.0)
    return {
        "sales": int(data[0].get("sales_count") or 0),
        "revenue": round(revenue, 2),
    }


async def _top_products(limit: int) -> list:
    pipeline = [
        {"$match": SALES_FILTER},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "product_name": {"$first": "$items.product_name"},
                "units_sold": {"$sum": "$items.quantity"},
                "revenue": {
                    "$sum": {"$multiply": ["$items.price", "$items.quantity"]}
                },
            }
        },
        {"$sort": {"units_sold": -1}},
        {"$limit": limit},
    ]
    data = await orders_collection.aggregate(pipeline).to_list(limit)
    return [
        {
            "product_id": item.get("_id"),
            "product_name": item.get("product_name"),
            "units_sold": int(item.get("units_sold") or 0),
            "revenue": round(float(item.get("revenue") or 0.0), 2),
        }
        for item in data
    ]


@dashboard_router.get("/overview")
@limiter.limit(RATE_LIMITS["dashboard_read"])
async def get_dashboard_overview(
    request: Request,
):
    local_now = datetime.utcnow().replace(tzinfo=timezone.utc)

    start_of_day = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
    start_of_month = start_of_day.replace(day=1)

    end_utc = _to_utc_naive(local_now)
    day_start_utc = _to_utc_naive(start_of_day)
    week_start_utc = _to_utc_naive(start_of_week)
    month_start_utc = _to_utc_naive(start_of_month)

    total = await _aggregate_sales(dict(SALES_FILTER))
    daily = await _aggregate_sales(
        {**SALES_FILTER, "created_at": {"$gte": day_start_utc, "$lt": end_utc}}
    )
    weekly = await _aggregate_sales(
        {**SALES_FILTER, "created_at": {"$gte": week_start_utc, "$lt": end_utc}}
    )
    monthly = await _aggregate_sales(
        {**SALES_FILTER, "created_at": {"$gte": month_start_utc, "$lt": end_utc}}
    )
    top_products = await _top_products(10)

    return {
        "as_of": local_now.isoformat(),
        "total": total,
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "top_products": top_products,
    }
