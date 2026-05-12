# 🗄️ Database Schema Documentation - WHAT2EAT

Tài liệu này mô tả cấu trúc cơ sở dữ liệu quan hệ (Relational Database) cho nền tảng WHAT2EAT. Hệ thống bao gồm **12 bảng dữ liệu chính** được thiết kế để đáp ứng các yêu cầu nghiệp vụ: quản lý người dùng, hồ sơ nhà hàng, đặt bàn trực tuyến, lưu trữ dữ liệu phục vụ cho mô hình AI gợi ý, hệ thống thông báo, và quản lý sức chứa linh hoạt.

---

## 1. Bảng `Users`

Đóng vai trò **Authentication & Identity** thuần túy — chỉ lưu thông tin định danh, xác thực và phân quyền. Dữ liệu profile mở rộng theo từng role được tách ra các bảng riêng: `CustomerProfiles` và `OwnerProfiles`.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `user_id` | UUID | PRIMARY KEY | Định danh duy nhất của người dùng |
| `full_name` | VARCHAR(255) | NOT NULL | Họ và tên người dùng |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Email đăng nhập |
| `password_hash` | VARCHAR(255) | NULL | Mật khẩu đã được băm (bcrypt). NULL nếu đăng nhập qua OAuth2 |
| `oauth_provider` | VARCHAR(50) | NULL | Nhà cung cấp OAuth2: `google`, `facebook`. NULL nếu đăng nhập thường |
| `oauth_id` | VARCHAR(255) | NULL | ID định danh từ phía nhà cung cấp OAuth2 |
| `role` | VARCHAR(50) | NOT NULL | Vai trò: `ADMIN`, `OWNER`, `CUSTOMER` |
| `avatar_url` | TEXT | NULL | Đường dẫn ảnh đại diện |
| `status` | VARCHAR(50) | DEFAULT 'ACTIVE' | Trạng thái tài khoản: `ACTIVE` (hoạt động), `BANNED` (bị khóa) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo tài khoản |

> **Ghi chú thiết kế:** Bảng `Users` chỉ đảm nhiệm vai trò định danh (Single Responsibility). Mỗi khi một `CUSTOMER` hoặc `OWNER` đăng ký, hệ thống tự động tạo một bản ghi tương ứng trong `CustomerProfiles` hoặc `OwnerProfiles`. Với `ADMIN`, các thông tin bổ sung ít và ổn định nên không cần bảng profile riêng.

---

## 2. Bảng `CustomerProfiles`

Lưu trữ thông tin profile mở rộng dành riêng cho Khách hàng. Quan hệ 1-1 với bảng `Users`.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `customer_id` | UUID | PRIMARY KEY, FOREIGN KEY | Liên kết 1-1 với `user_id` trong bảng `Users` |
| `dietary_preferences` | JSONB | NULL | Sở thích/hạn chế ăn uống. VD: `["chay", "không hải sản", "dị ứng đậu phộng"]` |
| `loyalty_points` | INT | DEFAULT 0 | Điểm tích lũy (dùng cho tính năng loyalty sau này) |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian cập nhật profile gần nhất |

> **Ghi chú:** `dietary_preferences` dạng JSONB cho phép lưu nhiều ràng buộc ăn uống linh hoạt — dữ liệu này được AI sử dụng để lọc gợi ý nhà hàng/món ăn phù hợp hơn với từng người dùng.

---

## 3. Bảng `OwnerProfiles`

Lưu trữ thông tin pháp lý và kinh doanh dành riêng cho Chủ nhà hàng. Quan hệ 1-1 với bảng `Users`.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `owner_id` | UUID | PRIMARY KEY, FOREIGN KEY | Liên kết 1-1 với `user_id` trong bảng `Users` |
| `tax_id` | VARCHAR(20) | NULL | Mã số thuế doanh nghiệp |
| `business_license` | VARCHAR(100) | NULL | Số giấy phép kinh doanh |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian cập nhật profile gần nhất |

> **Ghi chú:** Tách thông tin pháp lý ra khỏi `Users` giúp Admin có thể quản lý và xác minh tư cách pháp nhân của Chủ nhà hàng độc lập với quy trình xác thực tài khoản.

---

## 4. Bảng `Restaurants`

Lưu trữ hồ sơ thông tin chi tiết của các nhà hàng. Dữ liệu này phải trải qua quá trình kiểm duyệt từ Admin trước khi hiển thị công khai.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `restaurant_id` | UUID | PRIMARY KEY | Định danh duy nhất của nhà hàng |
| `owner_id` | UUID | FOREIGN KEY | Liên kết với `user_id` của chủ nhà hàng |
| `name` | VARCHAR(255) | NOT NULL | Tên nhà hàng |
| `address` | TEXT | NOT NULL | Địa chỉ chi tiết dạng văn bản |
| `latitude` | DECIMAL(9,6) | NULL | Vĩ độ địa lý. VD: `10.762622` |
| `longitude` | DECIMAL(9,6) | NULL | Kinh độ địa lý. VD: `106.660172` |
| `phone` | VARCHAR(20) | NOT NULL | Số điện thoại liên hệ |
| `description` | TEXT | NULL | Mô tả không gian quán |
| `open_hours` | JSONB | NULL | Giờ mở cửa theo từng ngày. VD: `{"mon": {"open": "08:00", "close": "22:00"}, "tue": ...}` |
| `images` | JSONB | NULL | Bộ sưu tập hình ảnh không gian/món ăn |
| `cuisine_type` | VARCHAR(100) | NULL | Loại ẩm thực. VD: `Lẩu`, `Cơm`, `Cà phê`, `Nhật`, `Hải sản` |
| `price_range` | VARCHAR(20) | NULL | Mức giá: `cheap` (dưới 100k), `mid` (100k–300k), `expensive` (trên 300k) |
| `average_rating` | DECIMAL(3,2) | DEFAULT 0.0 | Điểm đánh giá trung bình (tự động cập nhật khi có review mới được duyệt) |
| `status` | VARCHAR(50) | DEFAULT 'PENDING' | Trạng thái kiểm duyệt: `PENDING`, `APPROVED`, `REJECTED` |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian cập nhật hồ sơ gần nhất |

> **Ghi chú:** Thêm `latitude` và `longitude` kiểu `DECIMAL(9,6)` để hỗ trợ tìm kiếm theo vị trí ("quán gần đây", "gần Quận 1"). Với PostgreSQL/Supabase, hai cột này cho phép tính khoảng cách bằng công thức Haversine đủ dùng cho phase hiện tại. **Định hướng dài hạn:** Khi lượng dữ liệu lớn, có thể kích hoạt extension **PostGIS** và thêm cột `location GEOMETRY(Point, 4326)` để dùng spatial index `ST_Distance` với tốc độ vượt trội hơn nhiều so với tính toán trên DECIMAL.


---

## 5. Bảng `MenuItems`

Quản lý danh sách các món ăn thuộc từng nhà hàng. Hỗ trợ theo dõi trạng thái còn/hết hàng theo thời gian thực.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `item_id` | UUID | PRIMARY KEY | Định danh duy nhất của món ăn |
| `restaurant_id` | UUID | FOREIGN KEY | Liên kết với nhà hàng sở hữu món ăn |
| `name` | VARCHAR(255) | NOT NULL | Tên món ăn |
| `description` | TEXT | NULL | Mô tả chi tiết nguyên liệu/hương vị |
| `price` | DECIMAL(10,2) | NOT NULL | Giá bán |
| `category` | VARCHAR(100) | NULL | Phân loại: Đồ ăn, Nước uống, Combo... |
| `image_url` | TEXT | NULL | Hình ảnh minh họa |
| `is_available` | BOOLEAN | DEFAULT TRUE | Trạng thái phục vụ (TRUE: Còn hàng, FALSE: Hết hàng) |

---

## 6. Bảng `Capacities`

Lưu trữ thiết lập về sức chứa tối đa của nhà hàng theo từng khung giờ trong tuần để ngăn chặn tình trạng đặt vượt quá số ghế (Overbooking).

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `capacity_id` | UUID | PRIMARY KEY | Định danh duy nhất của thiết lập |
| `restaurant_id` | UUID | FOREIGN KEY | Liên kết với nhà hàng |
| `day_of_week` | INT | NOT NULL | Ngày trong tuần (0=CN, 1=T2, ..., 6=T7) |
| `start_time` | TIME | NOT NULL | Khung giờ bắt đầu |
| `end_time` | TIME | NOT NULL | Khung giờ kết thúc |
| `max_capacity` | INT | NOT NULL | Số lượng khách tối đa cho khung giờ này (0 = tạm ngừng nhận đặt chỗ) |

**Ràng buộc bổ sung:**
```sql
CONSTRAINT unique_capacity UNIQUE (restaurant_id, day_of_week, start_time, end_time)
```

> **Ghi chú:** Thêm ràng buộc `UNIQUE` để ngăn chặn việc insert trùng khung giờ cho cùng một nhà hàng — nếu không có ràng buộc này, logic kiểm tra overbooking sẽ tính sai tổng số đặt chỗ. Đổi `day_of_week` từ NULL thành NOT NULL vì đây là trường bắt buộc theo logic nghiệp vụ. Bảng này chỉ lưu **lịch trình mặc định theo tuần** — các trường hợp ngoại lệ (ngày lễ, Tết, bao trọn quán) được xử lý bởi bảng `CapacityOverrides`.

---

## 7. Bảng `CapacityOverrides`

Lưu các trường hợp ngoại lệ về sức chứa cho một **ngày cụ thể**, ghi đè lên lịch trình mặc định trong bảng `Capacities`. Logic kiểm tra bàn trống sẽ **ưu tiên bảng này trước**, nếu không có bản ghi phù hợp mới fallback về `Capacities`.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `override_id` | UUID | PRIMARY KEY | Định danh duy nhất của bản ghi ngoại lệ |
| `restaurant_id` | UUID | FOREIGN KEY | Nhà hàng áp dụng ngoại lệ |
| `override_date` | DATE | NOT NULL | Ngày cụ thể áp dụng ngoại lệ. VD: `2025-01-29` (mùng 1 Tết) |
| `start_time` | TIME | NOT NULL | Khung giờ bắt đầu |
| `end_time` | TIME | NOT NULL | Khung giờ kết thúc |
| `max_capacity` | INT | NOT NULL | Sức chứa mới cho ngày/khung giờ này (0 = đóng cửa/không nhận đặt chỗ) |
| `note` | TEXT | NULL | Ghi chú lý do. VD: `"Nghỉ Tết Nguyên Đán"`, `"Bao trọn gói sự kiện"` |

**Ràng buộc bổ sung:**
```sql
CONSTRAINT unique_override UNIQUE (restaurant_id, override_date, start_time, end_time)
```

**Ví dụ logic kiểm tra bàn trống tại backend:**
```
1. Tìm trong CapacityOverrides với (restaurant_id, date, time slot)
2. Nếu tồn tại → dùng max_capacity từ Override
3. Nếu không → fallback về Capacities theo (restaurant_id, day_of_week, time slot)
```

> **Ghi chú:** Bảng này được tạo mới để xử lý các ngoại lệ vận hành thực tế mà lịch trình `Capacities` cố định không thể bao quát được: ngày lễ, Tết, đóng cửa đột xuất, hoặc bao trọn gói sự kiện. Thiết kế này đảm bảo lịch trình gốc không bị ảnh hưởng khi có thay đổi tạm thời.

---

## 8. Bảng `Reservations`

Ghi nhận toàn bộ các yêu cầu đặt bàn trực tuyến từ Khách hàng đến Nhà hàng.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `reservation_id` | UUID | PRIMARY KEY | Định danh duy nhất của đơn đặt bàn |
| `customer_id` | UUID | FOREIGN KEY | Người dùng thực hiện đặt bàn |
| `restaurant_id` | UUID | FOREIGN KEY | Nhà hàng nhận đơn đặt |
| `reservation_time` | TIMESTAMP | NOT NULL | Thời gian khách dự kiến đến |
| `guest_count` | INT | NOT NULL | Số lượng khách |
| `notes` | TEXT | NULL | Ghi chú thêm (vd: cần ghế trẻ em, dị ứng thực phẩm) |
| `status` | VARCHAR(50) | DEFAULT 'PENDING' | Trạng thái: `PENDING` (chờ xác nhận), `CONFIRMED` (đã xác nhận), `REJECTED` (từ chối), `CANCELLED` (đã hủy) |
| `rejection_reason` | TEXT | NULL | Lý do từ chối (do Chủ nhà hàng điền khi chọn REJECTED) |

> **Ghi chú:** Thêm `rejection_reason` để lưu lý do từ chối theo yêu cầu use case U012 — Chủ nhà hàng phải nhập lý do khi từ chối, và lý do này phải được thông báo đến Khách hàng.

---

## 9. Bảng `Reviews`

Lưu trữ đánh giá trải nghiệm của khách hàng sau khi dùng bữa. Nội dung này cũng cần được kiểm duyệt.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `review_id` | UUID | PRIMARY KEY | Định danh duy nhất của đánh giá |
| `customer_id` | UUID | FOREIGN KEY | Khách hàng viết đánh giá |
| `restaurant_id` | UUID | FOREIGN KEY | Nhà hàng được đánh giá |
| `reservation_id` | UUID | FOREIGN KEY, UNIQUE | Đánh giá được gắn với đơn đặt bàn (mỗi đơn chỉ được đánh giá 1 lần) |
| `rating` | INT | CHECK (rating >= 1 AND rating <= 5) | Điểm đánh giá từ 1 đến 5 sao |
| `comment` | TEXT | NULL | Nhận xét chi tiết |
| `status` | VARCHAR(50) | DEFAULT 'PENDING' | Trạng thái kiểm duyệt: `PENDING`, `APPROVED`, `REJECTED` |
| `rejection_reason` | TEXT | NULL | Lý do từ chối của Admin khi không duyệt review |

> **Ghi chú:** Thêm `UNIQUE` constraint trên `reservation_id` để đảm bảo mỗi đơn đặt bàn chỉ có đúng 1 review. Thêm `rejection_reason` để Admin có thể ghi lý do từ chối theo use case U014.

---

## 10. Bảng `Favorites`

Lưu danh sách các nhà hàng yêu thích của khách hàng để dễ dàng truy cập lại.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `favorite_id` | UUID | PRIMARY KEY | Định danh của bản ghi |
| `customer_id` | UUID | FOREIGN KEY | Liên kết với người dùng |
| `restaurant_id` | UUID | FOREIGN KEY | Liên kết với nhà hàng được yêu thích |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời điểm lưu yêu thích |

**Ràng buộc bổ sung:**
```sql
CONSTRAINT unique_favorite UNIQUE (customer_id, restaurant_id)
```

---

## 11. Bảng `SearchHistory`

Lưu lại lịch sử tìm kiếm thông qua trợ lý AI (ngôn ngữ tự nhiên) của khách hàng. Dữ liệu này hỗ trợ mô hình Machine Learning học thói quen người dùng để cá nhân hóa kết quả.

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `search_id` | UUID | PRIMARY KEY | Định danh lịch sử tìm kiếm |
| `customer_id` | UUID | FOREIGN KEY | Người dùng thực hiện tìm kiếm |
| `query_text` | TEXT | NOT NULL | Câu lệnh gốc người dùng đã nhập. VD: `"Quán lẩu trời mưa"` |
| `extracted_entities` | JSONB | NULL | Các thực thể AI phân tích được. VD: `{"type": "lẩu", "weather": "mưa", "price": "mid"}` |
| `result_restaurant_ids` | JSONB | NULL | Danh sách ID nhà hàng đã được trả về cho người dùng. VD: `["uuid1", "uuid2"]` |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian thực hiện tìm kiếm |

> **Ghi chú:** Thêm `result_restaurant_ids` để lưu lại kết quả AI đã gợi ý. Dữ liệu này cần thiết để mô hình học được mối tương quan giữa query → kết quả → hành vi người dùng. **Định hướng dài hạn (Agentic AI):** Khi hệ thống phát triển sang Semantic Search, có thể thêm extension **pgvector** vào PostgreSQL và bổ sung cột `embedding VECTOR(1536)` cho bảng `Restaurants` và `MenuItems`. Khi đó, thay vì match cứng qua `extracted_entities`, AI sẽ chuyển câu hỏi thành vector và tìm nhà hàng theo khoảng cách ngữ nghĩa — cho kết quả tự nhiên và chính xác hơn đáng kể.

---

## 12. Bảng `Notifications`

Lưu trữ tất cả thông báo trong hệ thống gửi đến người dùng, phục vụ cho các use case: xác nhận/từ chối đặt bàn (U012), duyệt/từ chối review (U014), cảnh báo sức chứa 80% (U011), kết quả khóa/mở khóa tài khoản (U015).

| Column Name | Data Type | Constraints | Description |
| --- | --- | --- | --- |
| `notification_id` | UUID | PRIMARY KEY | Định danh duy nhất của thông báo |
| `user_id` | UUID | FOREIGN KEY | Người nhận thông báo |
| `type` | VARCHAR(100) | NOT NULL | Loại thông báo: `RESERVATION_CONFIRMED`, `RESERVATION_REJECTED`, `REVIEW_APPROVED`, `REVIEW_REJECTED`, `CAPACITY_WARNING`, `ACCOUNT_BANNED`, `ACCOUNT_UNBANNED` |
| `title` | VARCHAR(255) | NOT NULL | Tiêu đề thông báo |
| `content` | TEXT | NOT NULL | Nội dung chi tiết thông báo |
| `reference_id` | UUID | NULL | ID của đối tượng liên quan (vd: `reservation_id`, `review_id`) |
| `is_read` | BOOLEAN | DEFAULT FALSE | Trạng thái đã đọc |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo thông báo |

> **Ghi chú:** Bảng này được tạo mới để đáp ứng yêu cầu thông báo xuyên suốt nhiều use case. Trường `reference_id` cho phép frontend điều hướng người dùng đến đúng màn hình liên quan khi họ nhấn vào thông báo.

---

## 📐 Sơ đồ quan hệ (ERD tóm tắt)

```
Users (auth only)
  ├── CustomerProfiles  (1-1, customer_id → user_id)
  ├── OwnerProfiles     (1-1, owner_id    → user_id)
  │
  └──────────────────── Restaurants (owner_id → Users)
                            │
                            ├── MenuItems
                            ├── Capacities          (UNIQUE: restaurant_id + day + time)
                            ├── CapacityOverrides   (UNIQUE: restaurant_id + date + time)

Users
  ├── Reservations (customer_id + restaurant_id)
  │       └── Reviews (reservation_id UNIQUE, customer_id + restaurant_id)
  │
  ├── Favorites (customer_id + restaurant_id, UNIQUE)
  ├── SearchHistory (customer_id)
  └── Notifications (user_id)
```

**Logic kiểm tra sức chứa (theo thứ tự ưu tiên):**
```
CapacityOverrides (ngày cụ thể)  →  có?  dùng override
                                 →  không? fallback về Capacities (lịch trình tuần)
```

