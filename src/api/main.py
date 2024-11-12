from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated
import firebase_admin
from firebase_admin import credentials
from fastapi import Depends, FastAPI
from neo4j import AsyncGraphDatabase
from config.settings import get_firebase_user_from_token, get_settings
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Async context manager for MongoDB connection."""
    settings = get_settings()
    URI = f"bolt://{settings.NEO4J_SERVICE}:7687"
    AUTH = (settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    async with AsyncGraphDatabase.driver(URI, auth=AUTH) as driver:
        async with driver.session(database="neo4j") as session:
            app.session = session
            print("Successfully connected to Neo4j DB")
            yield
            print("Successfully closed Neo4j connection")


app = FastAPI(
    title="REST API for MTG Synchronizer",
    version=get_settings().TAG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=[get_settings().FRONTEND_URL],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cred = credentials.Certificate("service-account.json")
firebase_admin.initialize_app(cred)

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "REST API for querying Neo4j database of 130k wine reviews from the Wine Enthusiast magazine"
    }

@app.get("/userid")
async def get_userid(user: Annotated[dict, Depends(get_firebase_user_from_token)]):
    """gets the firebase connected user"""
    return {"id": user["uid"]}
