from routers.admin_registration import admin_registration_router
from config.collection import admin_registartion_collection
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import ASCENDING
from routers.categories_router import categories_router
from routers.products_router import products_router
from routers.uploads_router import upload_router

app = FastAPI(title="RaviTeja Foods Backend")

# ── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def bootstrap_indexes():
    await admin_registartion_collection.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="uniq_admin_email",
    )


@app.get("/")
async def health_check():
    return {"message": "Raviteja Foods Backend is running"}


app.include_router(admin_registration_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(upload_router)