from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.user import User
from core.security import get_password_hash

def seed_admin():
    # Mở kết nối đến database
    db: Session = SessionLocal()
    try:
        # Email admin mặc định bạn muốn cấp
        admin_email = "admin@what2eat.com"
        
        # Kiểm tra xem admin này đã có trong DB chưa
        admin_user = db.query(User).filter(User.email == admin_email).first()

        if not admin_user:
            print("🚀 Hệ thống chưa có Admin. Đang tự động khởi tạo...")
            
            # Tạo tài khoản Admin mới với role="admin"
            new_admin = User(
                fullName="Super Admin",
                email=admin_email,
                phone="0000000000",
                password=get_password_hash("admin123456"), # Mật khẩu mặc định
                role="admin",
                status="active"
            )
            db.add(new_admin)
            db.commit()
            print("Đã tạo tài khoản Admin thành công!")
        else:
            print("Tài khoản Admin đã tồn tại. Bỏ qua bước khởi tạo.")
    finally:
        # Luôn nhớ đóng kết nối
        db.close()