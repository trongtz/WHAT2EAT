from pydantic import BaseModel
from typing import Optional

class BookingBase(BaseModel):
    restaurant_id: int
    booking_date: str
    booking_time: str
    number_of_people: int
    note: Optional[str] = None

class BookingCreate(BookingBase):
    pass # Frontend chỉ cần gửi các trường ở trên lên là đủ (customer_id ta sẽ tự lấy từ Token)

class BookingResponse(BookingBase):
    id: int
    customer_id: int
    status: str

    class Config:
        from_attributes = True