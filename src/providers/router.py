from fastapi import APIRouter

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.post("/")
async def create_provider():
    pass


@router.get("/")
async def list_providers(service_id: int | None = None):
    pass


@router.get("/{provider_id}")
async def get_provider(provider_id: int):
    pass


@router.patch("/{provider_id}")
async def update_provider(provider_id: int):
    pass


@router.delete("/{provider_id}")
async def delete_provider(provider_id: int):
    pass