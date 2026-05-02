from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.user import User
from models.restaurant import Restaurant
from core.security import get_password_hash

def seed_data():
    db: Session = SessionLocal()
    try:
        # Kiểm tra xem hệ thống đã có User nào chưa
        if db.query(User).first():
            print("Database đã có dữ liệu. Bỏ qua bước tạo dữ liệu mẫu.")
            return

        print("Đang khởi tạo bộ dữ liệu mẫu (Mock Data)...")

        # 1. TẠO 3 TÀI KHOẢN MẪU (Pass chung là: 123456)
        hashed_pw = get_password_hash("123456")
        
        admin = User(fullName="Super Admin", email="admin@what2eat.com", phone="0901", password=hashed_pw, role="admin")
        owner = User(fullName="Trần Chủ Quán", email="owner@what2eat.com", phone="0902", password=hashed_pw, role="owner")
        customer = User(fullName="Nguyễn Thực Khách", email="customer@what2eat.com", phone="0903", password=hashed_pw, role="customer")
        
        db.add_all([admin, owner, customer])
        db.commit() 
        # Cần commit ở đây để hệ thống sinh ra 'owner.id' cho bước tiếp theo

        # 2. TẠO NHÀ HÀNG MẪU (Gắn cho Owner vừa tạo)
        restaurants = [
            Restaurant(
                owner_id=owner.id, 
                name="Phở Bát Đàn Gia Truyền", 
                address="49 Bát Đàn, Hoàn Kiếm, Hà Nội", 
                phone="0123456789", 
                description="Phở bò chuẩn vị Bắc, nước dùng thanh ngọt.", 
                opening_time="06:00 - 10:00", 
                capacity=40, 
                status="approved", # Đã duyệt để test Frontend cho dễ
                image_url="https://images.unsplash.com/photo-1628294895950-9805252327bc"
            ),
            Restaurant(
                owner_id=owner.id, 
                name="Cơm Tấm Ba Ghiền", 
                address="84 Đặng Văn Ngữ, Phú Nhuận, TP.HCM", 
                phone="0987654321", 
                description="Sườn nướng than hoa siêu to khổng lồ.", 
                opening_time="07:00 - 21:00", 
                capacity=60, 
                status="approved",
                image_url="https://images.unsplash.com/photo-1626804475297-41609ea004eb"
            )
        ]
        
        db.add_all(restaurants)
        db.commit()

        print("Đã bơm dữ liệu mẫu thành công! Tất cả tài khoản đều dùng pass: 123456")

    finally:
        db.close()