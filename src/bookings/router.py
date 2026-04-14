from fastapi import APIRouter

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/")
async def create_booking():
    pass


@router.get("/")
async def list_bookings(user_id: int | None = None):
    pass


@router.get("/{booking_id}")
async def get_booking(booking_id: int):
    pass


@router.patch("/{booking_id}")
async def update_booking_status(booking_id: int):
    pass


@router.delete("/{booking_id}")
async def cancel_booking(booking_id: int):
    pass    