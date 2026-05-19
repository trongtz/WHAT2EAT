import pandas as pd
import uuid
import random
import json
from datetime import datetime

# Read existing files
df_owners_old = pd.read_csv('generated_owners.csv')
df_rest_old = pd.read_csv('generated_restaurant_range.csv')
df_menu_old = pd.read_csv('generated_menu.csv')
df_cap_old = pd.read_csv('generated_capacity.csv')

# Read new restaurants
df_rest_new = pd.read_csv('restaurants.csv')

sample_images = [
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80",
    "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=800&q=80",
    "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=800&q=80",
    "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=800&q=80",
    "https://images.unsplash.com/photo-1466978913421-bac2e5970564?w=800&q=80",
    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&q=80"
]

cuisine_types = ['Nhà hàng', 'Cà phê', 'Quán ăn nhỏ', 'Món ăn nhanh', 'Quán nhậu', 'Nhà hàng chay', 'Nhật Bản', 'Hàn Quốc', 'Trà sữa']
price_ranges = ['30000 - 50000', '50000 - 100000', '100000 - 200000', '200000 - 500000', '500000 - 1000000']
menu_categories = ['Đồ ăn', 'Nước uống', 'Combo']
time_slots = [
    {"start": "11:00", "end": "14:00", "max": 40},
    {"start": "17:00", "end": "22:00", "max": 60}
]

new_owners = []
new_restaurants = []
new_menus = []
new_caps = []

owner_start_idx = len(df_owners_old) + 1
updated_at_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

for idx, row in df_rest_new.iterrows():
    rest_id = str(uuid.uuid4())
    owner_id = str(uuid.uuid4())
    
    # 1. Fake Owner
    new_owners.append({
        'user_id': owner_id,
        'full_name': f"Chủ Quán {owner_start_idx + idx}",
        'email': f"owner{owner_start_idx + idx}@what2eat.com",
        'password_hash': "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6L6.S3Y3/5fKjX.W",
        'role': 'OWNER',
        'status': 'ACTIVE'
    })
    
    # 2. Fake Restaurant
    cuisine = random.choice(cuisine_types)
    new_restaurants.append({
        'restaurant_id': rest_id,
        'owner_id': owner_id,
        'name': row['name'],
        'address': f"TP. Hồ Chí Minh, Việt Nam", # generic fallback
        'latitude': row['lat'],
        'longitude': row['long'],
        'phone': f"090{random.randint(1000000, 9999999)}",
        'description': f"{row['name']} - Chuyên phục vụ các món {cuisine.lower()} ngon và chất lượng.",
        'open_hours': "08:00 - 22:00",
        'images': json.dumps([random.choice(sample_images)]),
        'cuisine_type': cuisine,
        'price_range': random.choice(price_ranges),
        'average_rating': round(random.uniform(3.5, 5.0), 1),
        'status': 'APPROVED',
        'updated_at': updated_at_str
    })
    
    # 3. Fake Menus (2 items per rest)
    for _ in range(2):
        new_menus.append({
            'item_id': str(uuid.uuid4()),
            'restaurant_id': rest_id,
            'name': f"Món đặc biệt {random.randint(1, 100)}",
            'description': "Mô tả món ăn thơm ngon hấp dẫn.",
            'price': float(random.randint(30, 200) * 1000),
            'category': random.choice(menu_categories),
            'image_url': 'https://via.placeholder.com/200x200',
            'is_available': True
        })
        
    # 4. Fake Capacities
    for day in range(7):
        for slot in time_slots:
            new_caps.append({
                'capacity_id': str(uuid.uuid4()),
                'restaurant_id': rest_id,
                'day_of_week': day,
                'start_time': slot['start'],
                'end_time': slot['end'],
                'max_capacity': slot['max'] + random.randint(-10, 20)
            })

# Convert to DataFrame
df_owners_added = pd.DataFrame(new_owners)
df_rest_added = pd.DataFrame(new_restaurants)
df_menu_added = pd.DataFrame(new_menus)
df_cap_added = pd.DataFrame(new_caps)

# Concatenate with old data
df_owners_final = pd.concat([df_owners_old, df_owners_added], ignore_index=True)
df_rest_final = pd.concat([df_rest_old, df_rest_added], ignore_index=True)
df_menu_final = pd.concat([df_menu_old, df_menu_added], ignore_index=True)
df_cap_final = pd.concat([df_cap_old, df_cap_added], ignore_index=True)

# Save to CSV
df_owners_final.to_csv('generated_owners_updated.csv', index=False)
df_rest_final.to_csv('generated_restaurant_range_updated.csv', index=False)
df_menu_final.to_csv('generated_menu_updated.csv', index=False)
df_cap_final.to_csv('generated_capacity_updated.csv', index=False)

print(f"Final Owners count: {len(df_owners_final)}")
print(f"Final Restaurants count: {len(df_rest_final)}")
print(f"Final Menus count: {len(df_menu_final)}")
print(f"Final Capacities count: {len(df_cap_final)}")