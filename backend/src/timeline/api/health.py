from fastapi import APIRouter
from timeline.ai.client import get_backend

router = APIRouter()


@router.get("/health")
async def health():
    backend = await get_backend()
    return {
        "status": "ok",
        "ai_backend": backend.name,
        "ai_available": await backend.is_available(),
    }
