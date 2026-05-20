from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "RaviTejaFoods")
client = AsyncIOMotorClient(MONGO_URL, tls=True, tlsAllowInvalidCertificates=True)
db = client[DB_NAME]
