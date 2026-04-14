from fastapi import APIRouter

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.post("/")
async def create_slot():
    pass


@router.get("/")
async def get_slots(provider_id: int, date: str):
    pass


@router.patch("/{slot_id}")
async def update_slot(slot_id: int):
    pass


@router.delete("/{slot_id}")
async def delete_slot(slot_id: int):
    pass