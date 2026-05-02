from pydantic import BaseModel
from typing import Optional

class DishBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    is_available: bool = True
    image_url: Optional[str] = None

class DishCreate(DishBase):
    # Khi tạo món ăn, Owner phải gửi lên ID của nhà hàng mà họ muốn thêm vào
    restaurant_id: int 

class DishResponse(DishBase):
    id: int
    restaurant_id: int

    class Config:
        from_attributes = True