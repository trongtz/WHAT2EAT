from __future__ import annotations

import csv
from pathlib import Path
from uuid import uuid4


RESTAURANTS_PATH = Path(__file__).resolve().parents[1] / "data" / "restaurants.csv"


DEMO_UPDATES = {
    "Student Station Coffee": {
        "description": "Student Station Coffee là quán cà phê yên tĩnh gần ĐH Khoa học Tự nhiên Linh Trung, có wifi, ổ cắm, phù hợp học bài và làm việc nhóm.",
        "price_range": "30000 - 70000",
        "rating_avg": "4.7",
    },
    "BoBaPop - Làng Đại Học": {
        "description": "BoBaPop - Làng Đại Học là quán trà sữa/cà phê gần khu ĐHQG, giá sinh viên, có wifi, phù hợp đi nhóm nhỏ sau giờ học.",
        "price_range": "25000 - 65000",
        "rating_avg": "4.6",
    },
    "Coffee House": {
        "description": "Coffee House là quán cà phê gần Làng Đại Học, có wifi, ổ cắm, phù hợp học bài và gặp bạn bè.",
        "price_range": "30000 - 80000",
        "rating_avg": "4.5",
    },
    "DORMITORY COFFEE & TEA": {
        "description": "DORMITORY COFFEE & TEA là cafe gần ký túc xá và ĐH KHTN, không gian yên tĩnh, có ổ cắm, wifi, hợp học bài.",
        "price_range": "25000 - 60000",
        "rating_avg": "4.6",
    },
    "Cafe Truyền Thuyết": {
        "description": "Cafe Truyền Thuyết là quán cà phê bình dân gần Làng Đại Học, không gian thoải mái, có wifi và ổ cắm.",
        "price_range": "25000 - 60000",
        "rating_avg": "4.5",
    },
    "Hup Coffe": {
        "description": "Hup Coffe là cafe gần ĐH KHTN Linh Trung, không gian thoải mái, phù hợp học nhóm.",
        "price_range": "25000 - 70000",
        "rating_avg": "4.3",
    },
    "Iwans coffee & Tea": {
        "description": "Iwans coffee & Tea là quán cà phê/trà gần khu ĐHQG, có wifi, ổ cắm, hợp ngồi học.",
        "price_range": "30000 - 80000",
        "rating_avg": "4.3",
    },
    "Cà Phê iCoffee": {
        "description": "Cà Phê iCoffee là cafe gần Thủ Đức/Làng Đại Học, giá sinh viên, phù hợp học bài.",
        "price_range": "25000 - 70000",
        "rating_avg": "4.2",
    },
    "The Zero Coffee": {
        "description": "The Zero Coffee là quán cà phê gần ĐH KHTN Linh Trung, phù hợp học bài, làm việc laptop, có wifi và ổ cắm.",
        "price_range": "30000 - 70000",
        "rating_avg": "4.5",
    },
    "An Tea & Coffee": {
        "description": "An Tea & Coffee là cafe ở Linh Trung, Thủ Đức, có wifi, ổ cắm, không gian yên tĩnh cho sinh viên học bài.",
        "price_range": "30000 - 80000",
        "rating_avg": "4.6",
    },
    "Feel Coffee & Tea Express": {
        "description": "Feel Coffee & Tea Express là quán cà phê/trà gần Linh Trung, giá mềm, có wifi, phù hợp ngồi nhanh hoặc học nhóm.",
        "price_range": "25000 - 60000",
        "rating_avg": "4.4",
    },
    "Cà phê A4": {
        "description": "Cà phê A4 là quán cà phê trong khu sinh viên ĐHQG, giá rẻ, thuận tiện học bài và gặp bạn bè.",
        "price_range": "20000 - 50000",
        "rating_avg": "4.2",
    },
    "Cafe A3": {
        "description": "Cafe A3 là quán cà phê sinh viên gần ký túc xá, giá rẻ, có wifi, phù hợp học nhóm.",
        "price_range": "20000 - 50000",
        "rating_avg": "4.2",
    },
    "86 Cafe & Milktea": {
        "description": "86 Cafe & Milktea là cafe/trà sữa gần Làng Đại Học, có wifi, ổ cắm và mức giá sinh viên.",
        "price_range": "25000 - 65000",
        "rating_avg": "4.5",
    },
    "Six Coffee": {
        "description": "Six Coffee là quán cà phê gần ĐHQG, không gian yên tĩnh, có wifi và ổ cắm, phù hợp học bài.",
        "price_range": "30000 - 70000",
        "rating_avg": "4.5",
    },
    "Cloud Coffee": {
        "description": "Cloud Coffee là quán cà phê gần Làng Đại Học, có wifi, ổ cắm, hợp học bài và làm việc.",
        "price_range": "30000 - 80000",
        "rating_avg": "4.2",
    },
    "Oxy": {
        "description": "Oxy là cafe gần khu sinh viên ĐHQG, không gian thoáng, giá dễ chịu.",
        "price_range": "25000 - 70000",
        "rating_avg": "4.1",
    },
    "Kôphin Coffee": {
        "description": "Kôphin Coffee là quán cà phê gần khu đại học, có wifi, ổ cắm, phù hợp làm việc laptop.",
        "price_range": "30000 - 70000",
        "rating_avg": "4.4",
    },
    "Jiangnam Coffee": {
        "description": "Jiangnam Coffee là cafe gần Làng Đại Học, không gian nhẹ nhàng, có wifi, hợp học bài và hẹn bạn.",
        "price_range": "30000 - 80000",
        "rating_avg": "4.4",
    },
    "Góc chill cafe": {
        "description": "Góc chill cafe là quán cafe ở Thủ Đức gần khu đại học, không gian thư giãn, phù hợp hẹn bạn.",
        "price_range": "30000 - 80000",
        "rating_avg": "4.2",
    },
    "Chill corner": {
        "description": "Chill corner là cafe gần khu ĐHQG, không gian nhẹ nhàng, phù hợp ngồi nói chuyện hoặc học nhóm.",
        "price_range": "30000 - 80000",
        "rating_avg": "4.3",
    },
    "Mì Cay Naga": {
        "description": "Mì Cay Naga là quán món Hàn gần ĐH Khoa học Tự nhiên Linh Trung, có mì cay, tokbokki, kimbap, giá sinh viên.",
        "price_range": "30000 - 80000",
        "rating_avg": "4.6",
    },
    "Seoul": {
        "description": "Seoul là quán món Hàn gần Làng Đại Học, có cơm trộn, kimbap, tokbokki, mì cay, phù hợp nhóm sinh viên.",
        "price_range": "45000 - 120000",
        "rating_avg": "4.7",
    },
    "Daegu": {
        "description": "Daegu là quán món Hàn Quốc gần ĐHQG, phục vụ tokbokki, kimbap, mì cay, gà sốt Hàn, hợp đi nhóm.",
        "price_range": "50000 - 130000",
        "rating_avg": "4.5",
    },
    "Woori Coffee": {
        "description": "Woori Coffee là quán cafe gần Làng Đại Học, có đồ uống, wifi, không gian nhẹ nhàng.",
        "price_range": "30000 - 80000",
        "rating_avg": "4.3",
    },
    "Panda House": {
        "description": "Panda House là quán món Hàn/ăn vặt gần Làng Đại Học, có tokbokki, kimbap, gà sốt, giá sinh viên.",
        "price_range": "35000 - 100000",
        "rating_avg": "4.2",
    },
    "Quán ăn vặt Hàn Quốc Tân Hòa": {
        "description": "Quán ăn vặt Hàn Quốc Tân Hòa gần ĐHQG, có tokbokki, kimbap, mì cay, phù hợp nhóm sinh viên.",
        "price_range": "30000 - 90000",
        "rating_avg": "4.3",
    },
    "Kimbap Sinh Viên": {
        "description": "Kimbap Sinh Viên là quán món Hàn bình dân gần Linh Trung, có kimbap, tokbokki và mì cay.",
        "price_range": "30000 - 85000",
        "rating_avg": "4.4",
    },
    "Quán Cơm Thành Tài": {
        "description": "Quán Cơm Thành Tài là quán cơm sinh viên gần ĐH KHTN Linh Trung, món Việt, giá rẻ, phù hợp ăn trưa.",
        "price_range": "25000 - 60000",
        "rating_avg": "4.3",
    },
    "IU Canteen": {
        "description": "IU Canteen là căn tin sinh viên gần khu ĐHQG, nhiều món ăn nhanh, cơm trưa, giá phù hợp sinh viên.",
        "price_range": "25000 - 70000",
        "rating_avg": "4.1",
    },
    "Canteen H6": {
        "description": "Canteen H6 là căn tin gần Bách Khoa cơ sở 2 và ĐH KHTN, phù hợp ăn trưa sinh viên, giá bình dân.",
        "price_range": "25000 - 60000",
        "rating_avg": "4.5",
    },
    "Nhà Hàng Cơm Chay 8k": {
        "description": "Nhà Hàng Cơm Chay 8k là quán chay/healthy gần Linh Trung, giá sinh viên, phù hợp ăn trưa nhẹ.",
        "price_range": "15000 - 50000",
        "rating_avg": "4.6",
    },
    "Bún Đậu Mắm Tôm Gánh Chi Nhánh II": {
        "description": "Bún Đậu Mắm Tôm Gánh Chi Nhánh II là quán món Việt gần Làng Đại Học, phù hợp đi nhóm sinh viên.",
        "price_range": "40000 - 100000",
        "rating_avg": "4.3",
    },
    "Bún đậu Thị Nở (cơ sở 5)": {
        "description": "Bún đậu Thị Nở cơ sở 5 là quán món Việt gần ĐHQG, giá sinh viên, phù hợp ăn nhóm.",
        "price_range": "40000 - 100000",
        "rating_avg": "4.2",
    },
}

DEMO_INSERTS = [
    {
        "name": "Kimbap Sinh Viên",
        "description": "Kimbap Sinh Viên là quán món Hàn bình dân gần Linh Trung, có kimbap, tokbokki và mì cay.",
        "address": "Đường Tô Vĩnh Diện, Đông Hòa, Dĩ An, Bình Dương",
        "latitude": "10.8904",
        "longitude": "106.8122",
        "price_range": "30000 - 85000",
        "rating_avg": "4.4",
    },
    {
        "name": "Quán ăn vặt Hàn Quốc Tân Hòa",
        "description": "Quán ăn vặt Hàn Quốc Tân Hòa gần ĐHQG, có tokbokki, kimbap, mì cay, phù hợp nhóm sinh viên.",
        "address": "Đường Tân Hòa, Đông Hòa, Dĩ An, Bình Dương",
        "latitude": "10.8917",
        "longitude": "106.8155",
        "price_range": "30000 - 90000",
        "rating_avg": "4.3",
    },
    {
        "name": "BBQ Sinh Viên Linh Trung",
        "description": "BBQ Sinh Viên Linh Trung là quán nướng bình dân gần ĐH Khoa học Tự nhiên, có thịt nướng, xiên que, lẩu nướng và combo nhóm giá sinh viên.",
        "address": "Đường Tân Hòa, Đông Hòa, Dĩ An, Bình Dương",
        "latitude": "10.8798",
        "longitude": "106.8061",
        "price_range": "59000 - 150000",
        "rating_avg": "4.5",
    },
]


def main() -> None:
    with RESTAURANTS_PATH.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
        fieldnames = list(rows[0].keys())

    updated = 0
    existing_names = {row["name"] for row in rows}
    for row in rows:
        patch = DEMO_UPDATES.get(row["name"])
        if not patch:
            continue
        row.update(patch)
        updated += 1

    inserted = 0
    template = rows[0]
    demo_owner_id = next((row["owner_id"] for row in rows if row.get("owner_id")), template["owner_id"])
    for item in DEMO_INSERTS:
        if item["name"] in existing_names:
            continue
        row = {fieldname: "" for fieldname in fieldnames}
        row.update(
            {
                "restaurant_id": str(uuid4()),
                "owner_id": demo_owner_id,
                "phone": "0900000000",
                "opening_hours": '{"mon": "08:00-22:00", "tue": "08:00-22:00", "wed": "08:00-22:00", "thu": "08:00-22:00", "fri": "08:00-22:00", "sat": "08:00-22:00", "sun": "08:00-22:00"}',
                "approval_status": "APPROVED",
                "is_active": "True",
                "created_at": "2026-05-28T00:00:00Z",
                "updated_at": "2026-05-28T00:00:00Z",
            }
        )
        row.update(item)
        rows.append(row)
        existing_names.add(item["name"])
        inserted += 1

    with RESTAURANTS_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print({"updated": updated, "inserted": inserted, "targeted": len(DEMO_UPDATES), "restaurants": len(rows)})


if __name__ == "__main__":
    main()
