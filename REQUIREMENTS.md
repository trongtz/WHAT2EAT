# Requirements

## Overview

Repository hien tai chua phan `frontend` duoc xay dung bang React + Vite.
Thu muc `backend` dang trong, co the bo sung sau neu mo rong he thong.

## Software Requirements

- Node.js 18 tro len
- npm 9 tro len
- Git de quan ly ma nguon va day len GitHub

## Project Structure

- `frontend/`: ung dung giao dien React/Vite
- `backend/`: thu muc du phong cho API/server

## Frontend Dependencies

Frontend su dung cac thu vien chinh:

- React
- Vite
- Axios
- React Router DOM
- Material UI
- Leaflet
- React Leaflet

Chi tiet phien ban duoc khai bao trong `frontend/package.json`.

## How To Run

1. Cai dependencies:

```bash
cd frontend
npm install
```

2. Chay moi truong development:

```bash
npm run dev
```

3. Build production:

```bash
npm run build
```

## Notes Before Pushing To GitHub

- Khong dua `node_modules/` len repository
- Khong dua `dist/` len repository neu khong can luu ban build
- Khong commit cac file `.env` chua thong tin nhay cam
- Nen cap nhat `README.md` mo ta de tai, cach cai dat va thanh vien nhom
