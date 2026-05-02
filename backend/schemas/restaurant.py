from pydantic import BaseModel
from typing import Optional

# 1. Base Schema: Chứa các trường chung nhất
class RestaurantBase(BaseModel):
    name: str
    address: str
    phone: str
    description: Optional[str] = None
    opening_time: Optional[str] = None
    capacity: int = 50
    image_url: Optional[str] = None

# 2. Schema dùng để TẠO nhà hàng (Frontend gửi lên)
class RestaurantCreate(RestaurantBase):
    # owner_id: int # Tạm thời bắt truyền owner_id, sau này ta sẽ lấy tự động từ Token
    pass

# 3. Schema dùng để TRẢ VỀ (Backend gửi cho Frontend)
class RestaurantResponse(RestaurantBase):
    id: int
    owner_id: int
    status: str

    class Config:
        # Cấu hình này giúp Pydantic hiểu được dữ liệu từ SQLAlchemy (ORM)
        from_attributes = True