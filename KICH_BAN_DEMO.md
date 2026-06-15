# Kich ban demo WHAT2EAT

## 1. Muc tieu demo

Tai lieu nay dung de demo he thong WHAT2EAT cho giao vien theo luong thuc te cua 3 vai tro:

- Khach hang: xem ban do nha hang, tim kiem, xem chi tiet, yeu thich, dat ban, xem lich su, danh gia, goi y bang AI, cap nhat ho so.
- Chu nha hang: dang ky chi nhanh, xem trang thai duyet, cap nhat nha hang da duyet, quan ly menu, xu ly dat ban, xem danh gia.
- Admin: xem tong quan he thong, duyet ho so nha hang, tu choi ho so nha hang, khoa hoac mo khoa tai khoan nguoi dung.

Nen demo tren trinh duyet desktop voi 2 tab:

- Tab 1: frontend `http://localhost:5173`
- Tab 2: API docs `http://localhost:8000/docs`

## 2. Chuan bi truoc khi demo

### 2.1. Kiem tra yeu cau cai dat

- Node.js 18 tro len.
- npm 9 tro len.
- Python moi truong da cai cac package trong `requirements.txt`.
- Docker Desktop neu chay PostgreSQL bang `docker-compose.yml`.

### 2.2. Chay database

Tai thu muc goc du an:

```bash
docker compose up -d postgres
```

Kiem tra container `what2eat_postgres` da chay va port local la `5434`.

### 2.3. Chay backend

Tai thu muc goc du an:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Mo nhanh `http://localhost:8000/`, neu thay thong bao `WHAT2EAT Backend is running!` la backend san sang.

Mo `http://localhost:8000/docs` de giao vien thay danh sach API theo nhom:

- Auth
- Profile
- Restaurants
- Reviews
- Favorites
- Bookings
- AI Recommendations
- AI Sessions
- Owner Dashboard
- Dishes
- Admin
- Check-ins
- Notifications
- Search History
- Taxonomy

### 2.4. Chay frontend

Tai thu muc `frontend`:

```bash
npm run dev
```

Mo `http://localhost:5173`.

### 2.5. Tai khoan demo

Neu database duoc seed tu `backend/data/users.csv` hien tai, cac email toi thieu `admin@what2eat.com`, `owner@what2eat.com`, `customer@what2eat.com` khong duoc tao vi file CSV da ton tai. Hay dung tai khoan that co trong bo seed hien tai hoac tai khoan da nap bang SQL test.

Tai khoan co trong `backend/data/users.csv` hien tai:

| Vai tro | Email | Mat khau | Ghi chu |
| --- | --- | --- | --- |
| Khach hang | `customer.demo@what2eat.com` | `123456` | Customer demo them truc tiep trong CSV |
| Khach hang | `student.khtn@what2eat.demo` | `123456` | User demo sinh vien trong CSV |
| Chu nha hang | `owner1@what2eat.com` | `123456` | Owner seed dau tien trong CSV |
| Chu nha hang | `owner2@what2eat.com` | `123456` | Owner seed thu hai trong CSV |

File `restaurant_management_test_seed.sql` co them cac tai khoan test mat khau `123456` neu da chay file nay vao database:

| Vai tro | Email | Mat khau |
| --- | --- | --- |
| Chu nha hang | `rm-owner-test@what2eat.com` | `123456` |
| Chu nha hang | `rm-other-owner-test@what2eat.com` | `123456` |
| Khach hang | `rm-customer-test@what2eat.com` | `123456` |

Luu y: `backend/data/users.csv` hien tai khong co user vai tro `ADMIN`. Neu can demo admin, can chuan bi truoc mot tai khoan admin trong database hoac bo sung admin seed.

## 3. Mo dau demo

### 3.1. Gioi thieu bai toan

Noi ngan gon:

WHAT2EAT la ung dung goi y nha hang va dat ban. He thong gom frontend React, backend FastAPI va PostgreSQL. Nguoi dung co the tim nha hang theo vi tri, bo loc, luu yeu thich, dat ban, danh gia. Chu nha hang quan ly chi nhanh va menu. Admin duyet nha hang va quan ly tai khoan.

### 3.2. Gioi thieu kien truc

Mo API docs va noi:

- Frontend goi API qua `http://localhost:8000/api`.
- Backend gom cac router theo nghiep vu.
- Du lieu nha hang, menu, dat ban, danh gia, yeu thich duoc luu trong database.
- Mot so chuc nang co cache o frontend de tai nhanh hon.

## 4. Demo luong khach vang lai

Muc tieu: cho thay nguoi chua dang nhap van xem duoc nha hang va co the trai nghiem che do khach.

### 4.1. Xem trang chu va ban do

1. Mo `http://localhost:5173`.
2. Quan sat ban do nha hang o trang chu.
3. Neu trinh duyet hoi quyen vi tri, chon cho phep neu muon demo tinh nang gan vi tri hien tai.
4. Chi vao cac marker tren ban do de xem ten nha hang.
5. Bam vao mot marker hoac mot nha hang noi bat.
6. Man hinh hien modal thong tin nhanh: anh, diem danh gia, dia chi, so dien thoai, gio mo cua, ban trong, menu noi bat, danh gia gan day.
7. Bam `Xem trang chi tiet` de vao trang chi tiet nha hang.

Diem can nhan manh:

- Trang chu ket hop ban do va danh sach nha hang noi bat.
- Neu co toa do, he thong tinh khoang cach va sap xep nha hang gan nguoi dung.
- Khach chua dang nhap van co the xem thong tin cong khai.

### 4.2. Tim kiem va bo loc

1. Vao menu `Tim kiem`.
2. Nhap tu khoa, vi du `lau`, `cafe`, hoac ten mot nha hang dang hien thi.
3. Chon danh muc, vi du `Lau`, `Nhat Ban`, `Nuong`, `Do uong`.
4. Chon ngan sach, vi du `Duoi 100.000d`, `100.000d - 300.000d`, `Tren 300.000d`.
5. Bam `Ap dung`.
6. Mo mot ket qua bang nut `Xem ngay`.

Diem can nhan manh:

- Bo loc truyen xuong API search theo query, cuisine type va price range.
- URL co search params nen co the chia se hoac reload trang voi bo loc hien tai.

### 4.3. Thu thao tac can dang nhap

1. O trang chi tiet nha hang, bam `Luu yeu thich` khi chua dang nhap.
2. He thong hien thong bao yeu cau dang nhap.
3. Vao trang `Dat ban`, thu dien form va bam xac nhan khi chua dang nhap.
4. He thong hien thong bao yeu cau dang nhap truoc khi dat ban.

Diem can nhan manh:

- He thong phan biet chuc nang cong khai va chuc nang can tai khoan.
- Cac thao tac ghi du lieu that vao database can dang nhap.

## 5. Demo dang ky, dang nhap va che do khach

### 5.1. Dang ky tai khoan moi

1. Vao `Dang ky`.
2. Nhap ho ten, email moi, mat khau va xac nhan mat khau.
3. Chon vai tro `Khach hang`.
4. Bam `Tao tai khoan`.
5. He thong chuyen ve trang dang nhap va hien thong bao dang ky thanh cong.

Sau do co the noi:

- Form co validate cac truong bat buoc.
- Vai tro duoc chon ngay khi dang ky.
- Tai khoan customer duoc dung cho luong dat ban, yeu thich va danh gia.

### 5.2. Dang nhap tai khoan khach hang

1. Vao `Dang nhap`.
2. Nhap email va mat khau cua tai khoan khach hang.
3. Bam `Dang nhap`.
4. He thong dua ve trang chu.
5. Mo menu ho so de xac nhan thong tin nguoi dung dang dang nhap.

### 5.3. Che do khach

1. Dang xuat.
2. Vao `Dang nhap`.
3. Bam `Vao voi tu cach Khach`.
4. He thong dua ve trang chu voi mot phien khach tam thoi.
5. Thu luu yeu thich hoac dat ban.
6. Giai thich: du lieu che do khach chi luu trong phien trinh duyet, khong ghi vao database.

## 6. Demo luong khach hang da dang nhap

### 6.1. Luu va bo yeu thich

1. Dang nhap bang tai khoan khach hang.
2. Vao trang chu hoac trang tim kiem.
3. Chon mot nha hang.
4. Bam `Luu yeu thich`.
5. Vao menu `Yeu thich`.
6. Kiem tra nha hang vua luu xuat hien trong danh sach.
7. Bam lai thao tac yeu thich de bo luu.
8. Kiem tra danh sach duoc cap nhat.

Diem can nhan manh:

- Yeu thich duoc luu theo customer.
- Trang yeu thich goi API lay danh sach nha hang da luu.

### 6.2. Dat ban

1. Vao chi tiet mot nha hang.
2. Bam `Dat ban ngay`.
3. Form dat ban se tu dien nha hang neu di tu trang chi tiet.
4. Chon ngay trong tuong lai.
5. Chon gio.
6. Nhap so khach, vi du `2` hoac `4`.
7. Nhap ghi chu, vi du `Can ban gan cua so`.
8. Bam `Xac nhan dat ban`.
9. He thong hien thong bao dat ban thanh cong.

Diem can nhan manh:

- Form co validate ngay, gio, so khach va nha hang.
- Backend tao reservation voi trang thai ban dau thuong la cho duyet.
- Sau khi dat ban, du lieu se xuat hien cho chu nha hang xu ly.

### 6.3. Xem lich su dat ban

1. Vao `Lich su dat ban`.
2. Kiem tra booking vua tao.
3. Noi ro cac thong tin hien thi: nha hang, ngay gio, so khach, ghi chu, trang thai.
4. Cho giao vien thay trang nay tu dong refresh dinh ky de cap nhat trang thai khi owner xac nhan hoac tu choi.

### 6.4. Danh gia nha hang

1. Vao `Danh gia`.
2. Chon nha hang.
3. Chon diem danh gia.
4. Nhap nhan xet, vi du `Do an ngon, khong gian sach se`.
5. Bam `Gui danh gia`.
6. Mo lai trang chi tiet nha hang de xem danh gia gan day.

Diem can nhan manh:

- Danh gia gan voi customer va restaurant.
- Diem danh gia anh huong den thong tin hien thi cua nha hang.

### 6.5. Cap nhat ho so

1. Vao `Ho so`.
2. Bam `Chinh sua ho so`.
3. Thay doi ho ten hoac email.
4. Bam `Luu thay doi`.
5. Kiem tra thong tin tren trang ho so duoc cap nhat.

Diem can nhan manh:

- Ho so dung API `/profile/me`.
- He thong luu lai thong tin user trong phien dang nhap.

## 7. Demo goi y nha hang bang AI

### 7.1. Goi y co vi tri

1. Dang nhap bang tai khoan khach hang hoac che do khach.
2. Vao `AI goi y`.
3. Neu trinh duyet hoi quyen vi tri, chon cho phep.
4. Nhap cau hoi mau:

```text
Goi y nha hang am cung cho buoi hen ho gan Quan 1, ngan sach 300k, con ban cho 2 nguoi luc 19h.
```

5. Bam `Send`.
6. Quan sat khung chat tra loi va cot danh sach nha hang duoc goi y.
7. Bam vao mot nha hang trong danh sach goi y de xem chi tiet.

Diem can nhan manh:

- Prompt duoc gui len API `/ai/recommend`.
- He thong co the gui kem toa do hien tai neu trinh duyet cho phep.
- Ket qua gom noi dung tra loi, session id va danh sach nha hang phu hop.

### 7.2. Goi y fallback khi AI khong phan hoi

Neu backend AI hoac OpenAI key khong san sang:

1. Van nhap prompt nhu tren.
2. He thong se thu fallback bang danh sach nha hang co san.
3. Giai thich: fallback giup demo khong bi dung khi dich vu AI ngoai bi loi.

### 7.3. Tao phien chat moi

1. Bam `New Chat`.
2. Nhap prompt khac:

```text
Tim quan ca phe yen tinh de lam viec, gia re, gan trung tam.
```

3. Quan sat lich su chat duoc reset va ket qua moi duoc hien thi.

## 8. Demo luong chu nha hang

### 8.1. Dang nhap owner

1. Dang xuat tai khoan hien tai.
2. Dang nhap bang tai khoan chu nha hang.
3. He thong tu dong chuyen den `/chu-nha-hang/dashboard`.
4. Gioi thieu khu vuc backoffice cua owner.

### 8.2. Dang ky chi nhanh moi

1. Vao `Nha hang`.
2. Bam `Dang ky chi nhanh`.
3. Nhap thong tin:
   - Ten chi nhanh.
   - Loai am thuc.
   - So dien thoai.
   - Khoang gia.
   - Dia chi.
   - Mo ta.
   - Danh sach anh, moi dong mot URL neu co.
   - Gio mo cua, vi du `08:00 - 22:00`.
   - So ban toi da.
4. Bam `Gui admin duyet`.
5. Kiem tra chi nhanh moi xuat hien voi trang thai cho duyet.

Diem can nhan manh:

- Owner khong tu y public nha hang.
- Ho so moi can admin duyet truoc khi duoc quan ly menu day du.

### 8.3. Xem chi tiet chi nhanh

1. Trong danh sach nha hang cua owner, bam `Xem chi tiet`.
2. Kiem tra thong tin chi nhanh, trang thai duyet, menu hien co.
3. Neu chi nhanh chua duyet, man hinh thong bao chua mo quyen cap nhat.
4. Neu chi nhanh da duyet, co nut them mon.

### 8.4. Cap nhat nha hang da duyet

1. Chon mot chi nhanh co trang thai da duyet.
2. Bam `Sua thong tin`.
3. Thay doi mo ta, gio mo cua, so ban toi da hoac anh.
4. Bam `Luu cap nhat`.
5. Mo lai chi tiet nha hang de kiem tra thong tin moi.

### 8.5. Them mon an

1. Vao `Menu`.
2. Chon chi nhanh da duyet.
3. Bam `Them mon`.
4. Nhap:
   - Ten mon.
   - Mo ta.
   - Gia.
   - Danh muc.
   - Anh mon an neu co.
   - Trang thai `Dang phuc vu`.
5. Bam `Them mon`.
6. Kiem tra mon moi xuat hien trong danh sach menu.
7. Mo trang chi tiet nha hang phia khach hang de thay menu moi.

### 8.6. Sua va xoa mon an

1. Trong trang `Menu`, chon mot mon.
2. Bam `Sua`.
3. Doi gia hoac doi trang thai thanh `Tam het`.
4. Bam `Luu thay doi`.
5. Kiem tra chip trang thai mon an thay doi.
6. Chon mot mon demo khong quan trong.
7. Bam `Xoa`.
8. Kiem tra mon bien mat khoi menu.

Nen noi voi giao vien:

- Xoa mon la thao tac thay doi du lieu, chi nen xoa mon demo.
- Trong san pham that co the them confirm modal de tranh xoa nham.

### 8.7. Xu ly dat ban

1. Vao `Dat ban` trong khu owner.
2. Tim booking vua tao o luong khach hang.
3. Kiem tra thong tin: ten khach, thoi gian, so khach, ghi chu, trang thai.
4. Bam `Xac nhan`.
5. Quay lai tab khach hang, vao `Lich su dat ban`.
6. Doi toi da 10 giay de trang refresh, kiem tra trang thai da cap nhat.
7. Quay lai owner, thu `Tu choi` voi mot booking khac neu co.
8. Thu `Cho duyet lai` de dua booking ve trang thai pending.

Diem can nhan manh:

- Owner quan ly booking cua cac nha hang thuoc ve minh.
- Trang lich su cua khach co refresh dinh ky de nhan trang thai moi.

### 8.8. Xem danh gia cua khach

1. Vao `Danh gia` trong khu owner.
2. Kiem tra danh sach danh gia duoc nhom theo nha hang.
3. Chi ra cac thong tin: ten khach, diem, noi dung, ngay tao.

## 9. Demo luong admin

### 9.1. Dang nhap admin

1. Dang xuat tai khoan owner.
2. Dang nhap bang tai khoan admin.
3. He thong tu dong chuyen den `/admin/dashboard`.

### 9.2. Xem tong quan he thong

1. O trang dashboard admin, chi ra cac the thong ke:
   - Tong nha hang.
   - Cho duyet.
   - Da duyet.
   - Chu nha hang.
2. Xem khu `Can xu ly hom nay`.
3. Xem chi so he thong:
   - Tong nguoi dung.
   - Khach hang.
   - Luot dat ban.
   - Danh gia trung binh.

Diem can nhan manh:

- Dashboard giup admin nam nhanh tinh trang he thong.
- So chi nhanh cho duyet lien quan truc tiep den trang duyet nha hang.

### 9.3. Duyet nha hang

1. Vao `Nha hang` trong khu admin.
2. Tim chi nhanh owner vua dang ky.
3. Kiem tra thong tin: ten, dia chi, owner, loai am thuc, khoang gia, mo ta.
4. Bam `Duyet chi nhanh`.
5. He thong hien thong bao da duyet.
6. Dang nhap lai owner.
7. Vao `Nha hang`, kiem tra chi nhanh chuyen sang trang thai da duyet.
8. Owner luc nay co the sua thong tin va them menu.

### 9.4. Tu choi nha hang

Nen dung mot chi nhanh demo khac de tranh anh huong luong da duyet.

1. Dang nhap owner va tao them mot chi nhanh moi voi du lieu thieu hoac khong hop le ve mat nghiep vu.
2. Dang nhap admin.
3. Vao `Nha hang`.
4. Bam `Tu choi`.
5. Dang nhap lai owner.
6. Kiem tra chi nhanh co trang thai bi tu choi va khong mo quyen quan ly menu.

### 9.5. Quan ly nguoi dung

1. Vao `Nguoi dung` trong khu admin.
2. Xem danh sach user theo vai tro customer, owner, admin.
3. Chon mot tai khoan demo khong phai admin dang dung.
4. Bam `Khoa tai khoan`.
5. Kiem tra trang thai doi sang tam khoa.
6. Bam `Mo khoa tai khoan`.
7. Kiem tra trang thai quay lai dang hoat dong.

Luu y khi demo:

- Khong khoa tai khoan admin dang dung.
- Nen dung tai khoan demo rieng de tranh mat quyen thao tac trong luc trinh bay.

## 10. Demo phan API docs

Sau khi demo UI, mo tab `http://localhost:8000/docs` va chi ra:

1. Nhom `Auth`: dang ky, dang nhap.
2. Nhom `Restaurants`: danh sach, tim kiem, chi tiet, menu, reviews.
3. Nhom `Bookings`: tao booking, lich su booking cua khach.
4. Nhom `Favorites`: luu va bo luu nha hang.
5. Nhom `Reviews`: tao danh gia.
6. Nhom `AI Recommendations`: goi y nha hang bang prompt.
7. Nhom `Owner Dashboard`: booking va review cua owner.
8. Nhom `Dishes`: them, sua, xoa menu item.
9. Nhom `Admin`: tong quan, duyet nha hang, quan ly users.
10. Cac nhom mo rong: check-ins, notifications, search history, taxonomy.

Neu giao vien hoi ve cac nhom mo rong chua co man hinh ro rang:

- Giai thich backend da co endpoint va model de mo rong.
- UI hien tai tap trung vao cac luong chinh cua bai toan: tim nha hang, dat ban, review, owner, admin va AI recommendation.

## 11. Thu tu demo de tranh loi

Nen demo theo thu tu nay:

1. Chay backend va frontend.
2. Mo trang chu, ban do, chi tiet nha hang.
3. Tim kiem va bo loc.
4. Dang nhap customer.
5. Luu yeu thich.
6. Dat ban.
7. AI goi y.
8. Danh gia.
9. Dang nhap owner.
10. Tao chi nhanh moi.
11. Dang nhap admin.
12. Duyet chi nhanh.
13. Dang nhap owner.
14. Them menu cho chi nhanh da duyet.
15. Xu ly booking.
16. Dang nhap customer.
17. Kiem tra lich su booking da doi trang thai.
18. Dang nhap admin.
19. Khoa va mo khoa tai khoan demo.
20. Mo API docs de tong ket backend.

## 12. Du lieu mau nen chuan bi

### 12.1. Prompt AI

```text
Goi y nha hang am cung cho buoi hen ho gan Quan 1, ngan sach 300k, con ban cho 2 nguoi luc 19h.
```

```text
Tim quan ca phe yen tinh de lam viec, gia re, gan trung tam.
```

```text
Toi muon an lau nong, di 4 nguoi, uu tien quan co danh gia tot.
```

### 12.2. Thong tin chi nhanh owner tao moi

| Truong | Gia tri goi y |
| --- | --- |
| Ten chi nhanh | WHAT2EAT Demo Bistro |
| Loai am thuc | Mon an Viet Nam |
| So dien thoai | 0909000000 |
| Khoang gia | 100k - 300k |
| Dia chi | 227 Nguyen Van Cu, Quan 5, TP.HCM |
| Mo ta | Chi nhanh demo phuc vu mon Viet hien dai, phu hop nhom ban va gia dinh. |
| Gio mo cua | 08:00 - 22:00 |
| So ban toi da | 20 |

### 12.3. Mon an owner tao moi

| Truong | Gia tri goi y |
| --- | --- |
| Ten mon | Com tam suon bi cha |
| Mo ta | Suon nuong, bi, cha trung va nuoc mam chua ngot. |
| Gia | 75000 |
| Danh muc | Mon chinh |
| Trang thai | Dang phuc vu |

### 12.4. Booking mau

| Truong | Gia tri goi y |
| --- | --- |
| Nha hang | Chon nha hang vua duyet hoac nha hang san co |
| Ngay | Ngay mai |
| Gio | 19:00 |
| So khach | 2 |
| Ghi chu | Can ban gan cua so |

### 12.5. Danh gia mau

| Truong | Gia tri goi y |
| --- | --- |
| Diem | 5 |
| Nhan xet | Mon an ngon, khong gian sach se, phuc vu nhanh. |

## 13. Cach xu ly tinh huong khi demo

### 13.1. Frontend bao loi khong ket noi backend

Kiem tra backend co dang chay o `http://localhost:8000` khong. File frontend dang cau hinh API base URL la `http://localhost:8000/api`.

### 13.2. Backend loi database

Kiem tra container PostgreSQL:

```bash
docker compose ps
```

Kiem tra bien moi truong backend da dung database local hay chua. Khong hien thi file moi truong chua thong tin nhay cam khi demo.

### 13.3. Khong co nha hang hien thi

Kiem tra database da seed du lieu chua. Co the mo API docs va goi thu endpoint danh sach nha hang de xac nhan backend co tra du lieu.

### 13.4. Khong lay duoc vi tri

Van demo duoc binh thuong. Giai thich rang neu khong co quyen vi tri, he thong hien danh sach va tim kiem khong loc theo vi tri hien tai.

### 13.5. AI khong tra loi

Dung fallback cua ung dung. Giai thich day la co che du phong khi dich vu AI ngoai hoac API key chua san sang.

### 13.6. Tai khoan demo khong dang nhap duoc

Dung chuc nang dang ky de tao customer va owner moi. Voi admin, can dung tai khoan admin da duoc nhom chuan bi trong database truoc buoi demo.

## 14. Ket luan demo

Ket thuc bang cac y chinh:

- He thong da co day du luong 3 vai tro: customer, owner, admin.
- Customer co the tim nha hang, xem ban do, dat ban, yeu thich, danh gia va nhan goi y AI.
- Owner co the dang ky chi nhanh, quan ly thong tin, menu, booking va danh gia.
- Admin co the quan sat tong quan, duyet nha hang va quan ly tai khoan.
- Backend co API docs ro rang, chia module theo nghiep vu va san sang mo rong cho check-in, notification, search history va taxonomy.
