import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")

async def test_db():
    try:
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000, tls=True, tlsAllowInvalidCertificates=True)
        db = client["RaviTejaFoods"]
        docs = await db["categories"].find({"business_type": "retail"}).to_list(length=None)
        print("Connected! Found:", len(docs))
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test_db())
