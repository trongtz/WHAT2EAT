# File: backend/core/import_data.py
import pandas as pd
import json
import os
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.user import User
from models.restaurant import Restaurant
from models.restaurant_taxonomy import CuisineCategory, RestaurantCuisine, RestaurantImage
from models.dish import MenuItem

def import_csv_data():
    db: Session = SessionLocal()
    
    # Xác định đường dẫn thư mục data (đảm bảo chạy đúng dù đứng ở đâu trong backend)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    try:
        print("--- Đang bắt đầu quá trình Import dữ liệu từ CSV ---")

        # 1. Import Owners (Bảng Users)
        owners_csv = os.path.join(data_dir, "generated_owners.csv")
        owners_df = pd.read_csv(owners_csv)
        owners_added = 0
        
        for _, row in owners_df.iterrows():
            exists = db.query(User).filter(User.user_id == str(row['user_id'])).first()
            if not exists:
                user = User(
                    user_id=str(row['user_id']),
                    full_name=str(row['full_name']),
                    email=str(row['email']),
                    password_hash=str(row['password_hash']),
                    role=str(row['role']),
                    status=str(row['status'])
                )
                db.add(user)
                owners_added += 1
        db.commit()
        print(f"✅ Đã import {owners_added} Owners mới.")

        # 2. Import Restaurants (Bảng Restaurants)
        rest_csv = os.path.join(data_dir, "generated_restaurant_range.csv")
        rest_df = pd.read_csv(rest_csv)
        rests_added = 0
        
        for _, row in rest_df.iterrows():
            exists = db.query(Restaurant).filter(Restaurant.restaurant_id == str(row['restaurant_id'])).first()
            if not exists:
                restaurant = Restaurant(
                    restaurant_id=str(row['restaurant_id']),
                    owner_id=str(row['owner_id']),
                    name=str(row['name']),
                    address=str(row['address']),
                    latitude=float(row['latitude']) if pd.notna(row['latitude']) else None,
                    longitude=float(row['longitude']) if pd.notna(row['longitude']) else None,
                    phone=str(row['phone']),
                    description=str(row['description']) if pd.notna(row['description']) else None,
                    opening_hours=str(row['open_hours']) if pd.notna(row['open_hours']) else None,
                    price_range=str(row['price_range']),
                    rating_avg=float(row['average_rating']),
                    approval_status=str(row['status'])
                )
                db.add(restaurant)
                db.flush()

                cuisine_name = str(row['cuisine_type']).strip() if pd.notna(row['cuisine_type']) else None
                if cuisine_name:
                    category = db.query(CuisineCategory).filter(CuisineCategory.name == cuisine_name).first()
                    if not category:
                        category = CuisineCategory(name=cuisine_name)
                        db.add(category)
                        db.flush()
                    db.add(RestaurantCuisine(restaurant_id=restaurant.restaurant_id, category_id=category.category_id))

                image_urls = json.loads(row['images']) if pd.notna(row['images']) else []
                for index, image_url in enumerate(image_urls):
                    db.add(
                        RestaurantImage(
                            restaurant_id=restaurant.restaurant_id,
                            image_url=image_url,
                            image_type="cover" if index == 0 else "general",
                        )
                    )
                rests_added += 1
        db.commit()
        print(f"✅ Đã import {rests_added} Restaurants mới.")

        # 3. Import Menu Items (Bảng MenuItems)
        menu_csv = os.path.join(data_dir, "generated_menu.csv")
        menu_df = pd.read_csv(menu_csv)
        menus_added = 0
        
        for _, row in menu_df.iterrows():
            exists = db.query(MenuItem).filter(MenuItem.item_id == str(row['item_id'])).first()
            if not exists:
                item = MenuItem(
                    item_id=str(row['item_id']),
                    restaurant_id=str(row['restaurant_id']),
                    name=str(row['name']),
                    description=str(row['description']) if pd.notna(row['description']) else None,
                    price=float(row['price']),
                    category=str(row['category']) if pd.notna(row['category']) else None,
                    image_url=str(row['image_url']) if pd.notna(row['image_url']) else None,
                    availability_status="AVAILABLE" if bool(row['is_available']) else "UNAVAILABLE"
                )
                db.add(item)
                menus_added += 1
        db.commit()
        print(f"✅ Đã import {menus_added} Menu Items mới.")

        print("--- Quá trình Import hoàn tất thành công! ---")

    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi khi import dữ liệu: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_data()
