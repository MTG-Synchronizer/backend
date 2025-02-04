from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials
from api.routers import collection, pool, suggestions, user
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from config.settings import get_settings
from neo4j import AsyncGraphDatabase

# Check if the default app is already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("service-account.json")
    firebase_admin.initialize_app(cred)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Async context manager for MongoDB connection."""
    settings = get_settings()
    URI = f"bolt://{settings.SERVER_HOST}:7687"
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
    allow_origins=get_settings().ALLOW_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Welcome to the MTG Synchronizer API",
    }

app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(pool.router, prefix="/pool", tags=["pool"])
app.include_router(collection.router, prefix="/collection", tags=["collection"])
app.include_router(suggestions.router, prefix="/suggestions", tags=["suggestions"])