from fastapi import APIRouter
from src.api.endpoints import index

api_router = APIRouter()
api_router.include_router(index.router)
