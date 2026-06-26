# WHAT2EAT

WHAT2EAT là một hệ thống hỗ trợ tìm kiếm, gợi ý và đặt bàn tại các nhà hàng, quán ăn thông minh. Hệ thống tích hợp bản đồ trực quan cùng công nghệ trí tuệ nhân tạo (AI Assistant) để đề xuất địa điểm ăn uống phù hợp nhất dựa trên nhu cầu, vị trí địa lý, khoảng cách, giá cả và khả năng phục vụ thực tế của các quán ăn.

## Các tính năng chính

### 1. Dành cho Khách hàng (Customer)
- Tìm kiếm và lọc nhà hàng theo tên, món ăn, địa chỉ, khoảng cách, điểm đánh giá.
- Bản đồ tương tác trực quan hiển thị danh sách nhà hàng xung quanh và chỉ đường.
- Trợ lý ảo AI hỗ trợ trò chuyện, phân tích yêu cầu tự nhiên (ví dụ: "quán lẩu dưới 100k cho 4 người trong bán kính 2km") và xếp hạng gợi ý thông minh dựa trên nhiều tiêu chí.
- Đặt bàn trực tuyến, chọn số lượng khách, thời gian và theo dõi lịch sử, trạng thái đặt bàn.
- Đánh giá, viết bình luận và chấm điểm cho các nhà hàng đã trải nghiệm.
- Lưu trữ các nhà hàng yêu thích để truy cập nhanh chóng.

### 2. Dành cho Chủ nhà hàng (Owner)
- Quản lý thông tin nhà hàng bao gồm tên, địa chỉ, liên hệ, giờ mở cửa và vị trí trên bản đồ.
- Thiết lập thời gian hoạt động và sức chứa tối đa của nhà hàng.
- Quản lý thực đơn: thêm mới món ăn, chỉnh sửa giá cả, mô tả và cập nhật trạng thái còn/hết món.
- Quản lý danh sách đặt bàn: tiếp nhận, duyệt hoặc từ chối yêu cầu đặt bàn từ khách hàng.
- Xác nhận check-in cho khách hàng khi đến quán để tự động cập nhật sức chứa thực tế còn lại.
- Theo dõi các đánh giá và phản hồi của khách hàng.

### 3. Dành cho Quản trị viên (Admin)
- Bảng điều khiển (Dashboard) thống kê hiệu suất hoạt động của hệ thống.
- Quản lý người dùng: xem danh sách và phân quyền tài khoản (Admin, Owner, Customer).
- Kiểm duyệt nhà hàng: xét duyệt hoặc từ chối các yêu cầu đăng ký nhà hàng mới từ Chủ nhà hàng.
- Xem số liệu phân tích và báo cáo doanh thu, lượt đặt bàn của hệ thống.

## Công nghệ sử dụng

### Frontend
- React 19 (JavaScript)
- Vite (Công cụ xây dựng và chạy môi trường dev nhanh chóng)
- Material UI (Bộ thư viện giao diện đáp ứng tốt trên nhiều thiết bị)
- React Leaflet và Leaflet (Bản đồ tương tác trực quan)
- Axios (Giao tiếp với Backend thông qua các RESTful API)
- React Router DOM 7 (Quản lý định tuyến và điều hướng trang)

### Backend
- FastAPI (Python Web Framework hiệu năng cao, xây dựng API nhanh chóng)
- SQLAlchemy (Mô hình hóa dữ liệu và tương tác với cơ sở dữ liệu qua ORM)
- PostgreSQL / Supabase (Hệ quản trị cơ sở dữ liệu quan hệ chính) hoặc SQLite (cho môi trường kiểm thử/phát triển cục bộ)
- Pydantic v2 (Xác thực và chuẩn hóa dữ liệu đầu vào/đầu ra)
- Passlib và Bcrypt (Mã hóa mật khẩu an toàn)
- Python-jose (Bảo mật thông tin và xác thực người dùng bằng JWT Token)
- OpenAI API (Sử dụng mô hình gpt-4o-mini để phân tích ý định tìm kiếm và tái xếp hạng gợi ý)

## Cấu trúc thư mục dự án

Cấu trúc thư mục tổng quát của dự án được tổ chức như sau:

```text
WHAT2EAT/
├── backend/
│   ├── api/             # Định nghĩa endpoints và phân luồng routes của API
│   │   ├── deps.py      # Dependency Injection (Trạm kiểm soát bảo mật)
│   │   └── routes/      # Danh sách các routes chính (auth, restaurants, dishes, bookings, ai)
│   ├── core/            # Cấu hình hệ thống, kết nối cơ sở dữ liệu, bảo mật và dữ liệu mẫu (seed data)
│   ├── crud/            # Thực hiện các truy vấn cơ sở dữ liệu trực tiếp (Create, Read, Update, Delete)
│   ├── data/            # Chứa các file dữ liệu tĩnh hoặc dữ liệu seed
│   ├── models/          # Định nghĩa cấu trúc các bảng trong cơ sở dữ liệu (SQLAlchemy ORM)
│   ├── schemas/         # Các Pydantic models để xác thực dữ liệu đầu vào/đầu ra
│   ├── scripts/         # Các tập lệnh kiểm thử nhanh (smoke tests) và reset cơ sở dữ liệu
│   ├── services/        # Tầng nghiệp vụ chính (ai_assistant, capacity_service, restaurant_service,...)
│   ├── main.py          # Điểm khởi chạy API chính (FastAPI), cấu hình CORS, kết nối DB
│   └── .env.example     # File ví dụ cấu hình các biến môi trường
├── frontend/
│   ├── public/          # Chứa các tài nguyên tĩnh công khai (logo, favicon,...)
│   ├── src/
│   │   ├── assets/      # Hình ảnh, font chữ và các tệp tĩnh dùng trong React
│   │   ├── components/  # Các thành phần giao diện nhỏ có thể tái sử dụng (Button, Input, Map,...)
│   │   ├── context/     # Quản lý trạng thái ứng dụng toàn cục (Auth, Theme,...)
│   │   ├── hooks/       # Custom React Hooks phục vụ nghiệp vụ hoặc tương tác
│   │   ├── layouts/     # Các mẫu bố cục trang (Navbar, Footer, Sidebar cho các vai trò)
│   │   ├── pages/       # Các trang giao diện chính (HomePage, AiRecommendationPage, BookingPage,...)
│   │   │   ├── admin/   # Các trang dành riêng cho Quản trị viên
│   │   │   └── owner/   # Các trang dành riêng cho Chủ nhà hàng
│   │   ├── routes/      # Cấu hình phân luồng và bảo vệ tuyến đường (Private / Public Route)
│   │   ├── services/    # Các API client thực hiện gửi yêu cầu HTTP đến Backend
│   │   ├── utils/       # Các hàm tiện ích bổ trợ (định dạng ngày tháng, tiền tệ,...)
│   │   ├── App.jsx      # Thành phần chính định nghĩa cấu trúc ứng dụng
│   │   └── main.jsx     # Điểm khởi tạo và render ứng dụng React lên DOM
│   ├── index.html       # Tệp HTML chính chứa phần tử gốc root của React
│   ├── package.json     # Liệt kê các thư viện dependencies và lệnh chạy ứng dụng
│   └── vite.config.js   # Cấu hình công cụ Vite
├── docker-compose.yml   # Cấu hình Docker để khởi chạy nhanh cơ sở dữ liệu PostgreSQL
├── requirements.txt     # Danh sách thư viện Python cần thiết cho Backend
└── README.md            # Tài liệu hướng dẫn sử dụng và thông tin dự án
```

## Hướng dẫn cài đặt và chạy ứng dụng

### Yêu cầu hệ thống
- Node.js (phiên bản 18 trở lên)
- npm (phiên bản 9 trở lên)
- Python (phiên bản 3.10 trở lên)
- Docker và Docker Compose (để chạy nhanh cơ sở dữ liệu Postgres cục bộ)

### 1. Thiết lập Cơ sở dữ liệu (PostgreSQL)
Để khởi chạy nhanh cơ sở dữ liệu PostgreSQL qua Docker:
Chạy lệnh sau tại thư mục gốc của dự án:
```bash
docker-compose up -d
```
Cơ sở dữ liệu sẽ chạy ở cổng 5434 với các thông số cấu hình mặc định được định nghĩa sẵn trong tệp docker-compose.yml.

### 2. Cài đặt và Khởi chạy Backend
Bước 1: Di chuyển vào thư mục backend:
```bash
cd backend
```

Bước 2: Tạo và kích hoạt môi trường ảo (virtual environment):
- Trên Windows (PowerShell):
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- Trên macOS/Linux:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

Bước 3: Cài đặt các thư viện phụ thuộc:
```bash
pip install -r ../requirements.txt
```

Bước 4: Cấu hình biến môi trường:
Sao chép tệp .env.example thành tệp .env và điều chỉnh các thông tin cấu hình phù hợp:
```env
DATABASE_URL=postgresql://what2eat:what2eat_dev@127.0.0.1:5434/what2eat_db
SECRET_KEY=khoa_bao_mat_cua_rieng_ban
OPENAI_API_KEY=sk-dien-khoa-openai-cua-ban-o-day
OPENAI_INTENT_PARSER=true
OPENAI_AGENTIC_RERANKER=true
```

Bước 5: Khởi chạy máy chủ Backend:
```bash
uvicorn main:app --reload
```
Máy chủ sẽ chạy tại địa chỉ http://127.0.0.1:8000. Bạn có thể kiểm tra và thử nghiệm các API thông qua tài liệu tương tác tại http://127.0.0.1:8000/docs.

### 3. Cài đặt và Khởi chạy Frontend
Bước 1: Di chuyển vào thư mục frontend:
```bash
cd frontend
```

Bước 2: Cài đặt các thư viện cần thiết:
```bash
npm install
```

Bước 3: Khởi chạy giao diện Frontend:
```bash
npm run dev
```
Giao diện ứng dụng sẽ chạy tại địa chỉ mặc định: http://localhost:5173.

## Kiểm thử hệ thống (Testing)

### Chạy kiểm thử đơn vị Backend
Để chạy các bộ kiểm thử đơn vị của Backend:
```bash
cd backend
python -m pytest ../tests/
```

### Chạy thử nghiệm nhanh gợi ý AI (Smoke Test)
Để kiểm tra tính năng phân tích ý định và xếp hạng gợi ý của AI Assistant:
```bash
cd backend
python scripts/smoke_ai_recommend.py "quán cafe yên tĩnh gần đây dưới 100k" --lat 10.7738 --lng 106.704 --limit 5
```
