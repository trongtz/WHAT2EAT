backend/
├── .env                 # (Bảo mật) Chứa biến môi trường (Database URL, Secret Key)
├── main.py              # Điểm entry của ứng dụng, cấu hình CORS, Error Handler, gộp Router
├── core/                # Thư mục chứa cấu hình lõi của hệ thống
│   ├── config.py        # Load và validate biến từ file .env
│   ├── database.py      # Thiết lập kết nối CSDL (SQLAlchemy Engine, Session)
│   └── security.py      # Logic bảo mật (Băm mật khẩu Bcrypt, mã hóa/giải mã JWT)
├── models/              # Thư mục định nghĩa CSDL (Database Schemas / ORM)
│   └── user.py          # Bảng Users (ID, fullName, email, password, role...)
├── schemas/             # Thư mục định nghĩa Pydantic Models (Validation Data)
│   └── auth.py          # Format Request (Login/Register) và Format Response trả về cho Frontend
├── crud/                # Thư mục chứa logic tương tác CSDL (Create, Read, Update, Delete)
│   └── user.py          # Chứa các hàm: get_user_by_email(), create_user()
└── api/                 # Thư mục định nghĩa các Endpoint (Controller)
    └── routes/          
        ├── api.py       # Master Router: Nơi gom tất cả các Router con lại
        ├── auth.py      # Xử lý /api/auth/login và /api/auth/register
        ├── restaurants.py # Xử lý /api/restaurants/...
        ├── bookings.py  # Xử lý /api/bookings/...
        ├── ai.py        # Xử lý /api/ai/...
        └── owner.py     # Xử lý /api/owner/...