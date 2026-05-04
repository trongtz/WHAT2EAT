``` bash
backend/
├── .env                 # (Bảo mật) Chứa biến môi trường (Supabase DB URL, OPENAI_API_KEY, Secret Key)
├── main.py              # Điểm entry, cấu hình CORS, Error Handler, tự động đồng bộ bảng lên Supabase, gộp Router
│
├── core/                # Thư mục chứa cấu hình lõi của hệ thống
│   ├── config.py        # Load và validate biến từ file .env (Sử dụng Pydantic BaseSettings)
│   ├── database.py      # Thiết lập kết nối CSDL PostgreSQL (Supabase) (SQLAlchemy Engine, Session)
│   ├── security.py      # Logic bảo mật (Băm mật khẩu Bcrypt, mã hóa/giải mã JWT)
│   └── init_db.py       # Tự động tạo sẵn dữ liệu mẫu demo(Admin, Owner, Customer, Nhà hàng)
│
├── models/              # Thư mục định nghĩa CSDL (Database Schemas / SQLAlchemy ORM)
│   ├── user.py          # Bảng users (Phân quyền role, liên kết 1-N với restaurants và bookings)
│   ├── restaurant.py    # Bảng restaurants (Thông tin quán, trạng thái pending/approved)
│   ├── dish.py          # Bảng dishes (Thực đơn của quán, trạng thái is_available)
│   └── booking.py       # Bảng bookings (Lịch đặt bàn, liên kết giữa Customer và Restaurant)
│
├── schemas/             # Thư mục định nghĩa Pydantic Models (Kiểm duyệt Data In/Out)
│   ├── auth.py          # Format Request (Login/Register) và Response trả về cho Frontend
│   ├── restaurant.py    # Schema kiểm tra dữ liệu tạo mới và hiển thị Nhà hàng
│   ├── dish.py          # Schema kiểm tra dữ liệu thêm Thực đơn
│   ├── booking.py       # Schema kiểm tra form Đặt bàn (BookingCreate, BookingResponse)
│   └── ai.py            # Schema định dạng câu hỏi và kết quả gợi ý trả về từ AI
│
├── crud/                # Thư mục chứa logic tương tác trực tiếp với Database (Queries)
│   ├── user.py          # Các hàm: get_user_by_email(), create_user()...
│   ├── restaurant.py    # Các hàm: get_restaurants(), create_restaurant()...
│   └── booking.py       # Các hàm: create_booking(), get_bookings(), update_booking_status()
│
├── services/            # Tầng logic nghiệp vụ phức tạp (Service Layer)
│   └── ai_service.py    # Khu vực làm việc độc lập của AI Engineer (Tích hợp OpenAI, tách biệt với API Router)
│
└── api/                 # Thư mục định nghĩa các cổng giao tiếp API (Controllers/Endpoints)
    ├── deps.py          # Dependency Injection (Trạm kiểm soát bảo mật chứa get_current_user và oauth2_scheme)
    └── routes/          
        ├── api.py       # Master Router: Nơi gom tất cả các Router con bên dưới lại
        ├── auth.py      # Xử lý /api/auth/register và /api/auth/login 
        ├── restaurants.py # Xử lý /api/restaurants/... (Public list, Thêm nhà hàng cho Owner)
        ├── dishes.py    # Xử lý /api/dishes/... (Thêm món, Quản lý thực đơn)
        ├── bookings.py  # Xử lý /api/bookings/... (Khách tạo đơn, Chủ quán duyệt đơn)
        └── ai.py        # Xử lý /api/ai/recommend (Cổng API gọi dịch vụ AI gợi ý nhà hàng)
```
