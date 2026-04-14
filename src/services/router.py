from fastapi import APIRouter

router = APIRouter(prefix="/services", tags=["Services"])


@router.post("/")
async def create_service():
    pass


@router.get("/")
async def list_services():
    pass


@router.get("/{service_id}")
async def get_service(service_id: int):
    pass


@router.patch("/{service_id}")
async def update_service(service_id: int):
    pass


@router.delete("/{service_id}")
async def delete_service(service_id: int):
    pass