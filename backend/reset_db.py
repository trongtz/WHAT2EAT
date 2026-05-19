from core.database import engine, Base
# Import tất cả models để SQLAlchemy biết cần xóa những bảng nào
import models.user
import models.customer_profile
import models.owner_profile
import models.restaurant
import models.dish
import models.booking
import models.capacity
import models.review
import models.favorite
import models.search_history
import models.notification

print("⚠️ Đang tiến hành xóa toàn bộ tables trong database...")

# Lệnh này sẽ DROP toàn bộ các bảng đã được định nghĩa trong Base
Base.metadata.drop_all(bind=engine)

print("✅ Đã dọn dẹp Database thành công!")
print("👉 Bây giờ hãy khởi động lại server (uvicorn main:app --reload) để tạo lại bảng và import data.")