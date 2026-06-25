# -*- coding: utf-8 -*-
"""
Cào các trường còn thiếu từ Google Maps:
  - address    (địa chỉ)
  - latitude   (vĩ độ — extract từ URL, không tốn request)
  - longitude  (kinh độ — extract từ URL, không tốn request)
  - reviews    (danh sách review text)

Input:  restaurant.csv
Output: restaurant_full.csv
"""

import re
import time
import json
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ============================================================
# CẤU HÌNH
# ============================================================
INPUT_FILE      = os.path.join("data", "raw", "restaurant.csv")
OUTPUT_FILE     = os.path.join("data", "raw", "restaurant_full.csv")
CHECKPOINT_FILE = os.path.join("data", "checkpoint", "checkpoint_crawl_maps.csv")
MAX_REVIEWS     = 50      # Số review tối đa mỗi nhà hàng
HEADLESS        = False    # False để quan sát, True để chạy ngầm

# ============================================================
# EXTRACT TỌA ĐỘ TỪ URL — Không tốn request
# ============================================================

def extract_coords_from_url(url: str) -> tuple:
    """
    Google Maps URL chứa tọa độ dạng: !8m2!3d{lat}!4d{lng}
    Ví dụ: !8m2!3d10.8472378!4d106.7685329
    → (10.8472378, 106.7685329)
    """
    if not url:
        return None, None
    match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

# ============================================================
# SETUP SELENIUM
# ============================================================

def create_driver(headless: bool = True) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--lang=vi")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    if headless:
        options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def get_address_and_reviews(driver: webdriver.Chrome, url: str,
                             max_reviews: int = 20) -> tuple:
    """
    Mở URL 1 lần, lấy address rồi chuyển sang tab review.
    Trả về (address, reviews_list)
    """
    address = ""
    reviews = []

    try:
        driver.get(url)
        # Chờ URL ổn định sau redirect
        try:
            WebDriverWait(driver, 15).until(
                lambda d: 'maps/place' in d.current_url
            )
        except:
            pass

        time.sleep(2)
        print(f"      [DEBUG] URL: {driver.current_url[:80]}")
        print(f"      [DEBUG] Title: {driver.title}")
        # --- Lấy address trên trang chính ---
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'button[data-item-id="address"]')
                )
            )
            addr_elem = driver.find_element(
                By.CSS_SELECTOR, 'button[data-item-id="address"]'
            )
            address = addr_elem.text.strip()
        except:
            try:
                addr_elem = driver.find_element(
                    By.CSS_SELECTOR, '[data-tooltip="Sao chép địa chỉ"]'
                )
                address = addr_elem.text.strip()
            except:
                pass

        # --- Click tab Review (không load lại URL) ---
        try:
            review_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(@aria-label, 'Bài đánh giá') "
                    "or contains(@aria-label, 'Reviews')]"
                ))
            )
            review_btn.click()
        except:
            try:
                first_result = driver.find_element(
                    By.CSS_SELECTOR, "a.hfpxzc"
                )
                first_result.click()
                review_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(@aria-label, 'Bài đánh giá') "
                        "or contains(@aria-label, 'Reviews')]"
                    ))
                )
                review_btn.click()
            except:
                return address, reviews

        # Chờ review xuất hiện
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jftiEf"))
            )
        except:
            return address, reviews

        # Tìm scrollable div
        scrollable_div = None
        selectors = ['div.m6QErb.DxyBCb', 'div[role="feed"]',
                     'div[tabindex="-1"]']
        for _ in range(15):
            for sel in selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.is_displayed():
                        scrollable_div = elem
                        break
                except:
                    pass
            if scrollable_div:
                break
            time.sleep(0.2)

        if not scrollable_div:
            return address, reviews

        # Scroll để load thêm review
        last_height = driver.execute_script(
            "return arguments[0].scrollHeight", scrollable_div
        )
        while True:
            review_elements = driver.find_elements(
                By.CLASS_NAME, 'jftiEf'
            )
            if len(review_elements) >= max_reviews:
                break
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight",
                scrollable_div
            )
            try:
                WebDriverWait(driver, 5).until(
                    lambda d: driver.execute_script(
                        "return arguments[0].scrollHeight", scrollable_div
                    ) > last_height
                )
                last_height = driver.execute_script(
                    "return arguments[0].scrollHeight", scrollable_div
                )
            except:
                break
        try:
            more_buttons = driver.find_elements(
                By.XPATH,
                "//button[@aria-label='Xem thêm' or "
                "@aria-label='See more' or "
                "contains(@class, 'w8nwRe')]"
            )
            for btn in more_buttons:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.1)
                except:
                    continue
        except:
            pass
        # Parse review texts
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        review_cards = soup.find_all('div', class_='jftiEf')
        for card in review_cards[:max_reviews]:
            try:
                text_elem = card.find('span', class_='wiI7pd')
                if not text_elem:
                    text_elem = card.find('div', class_='MyEned')
                if text_elem:
                    text = text_elem.text.strip()
                    if text:
                        reviews.append(text)
            except:
                continue

    except Exception as e:
        print(f"      [ERROR] {e}")

    return address, reviews

# ============================================================
# HÀM CHÍNH
# ============================================================

def run():
    os.makedirs(os.path.join("data", "raw"), exist_ok=True)
    os.makedirs(os.path.join("data", "checkpoint"), exist_ok=True)

    print(f"\n{'='*50}")
    print(f"CRAWL: Bổ sung address, tọa độ, reviews")
    print(f"{'='*50}")

    # --- Đọc file input ---
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Không tìm thấy {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    print(f"[INFO] Đọc được {len(df)} nhà hàng từ {INPUT_FILE}")

    # --- Khởi tạo cột nếu chưa có ---
    for col in ['address', 'latitude', 'longitude', 'reviews']:
        if col not in df.columns:
            df[col] = None

    # --- Extract tọa độ từ URL (không cần Selenium) ---
    print(f"\n[BƯỚC 1] Extract tọa độ từ URL...")
    coords_extracted = 0
    for idx, row in df.iterrows():
        if pd.isna(row.get('latitude')) or row.get('latitude') == '':
            lat, lng = extract_coords_from_url(str(row.get('url', '')))
            if lat and lng:
                df.at[idx, 'latitude']  = lat
                df.at[idx, 'longitude'] = lng
                coords_extracted += 1

    print(f"   → Extract được tọa độ: {coords_extracted} nhà hàng")

    # --- Load checkpoint nếu có ---
    done_ids = set()
    if os.path.exists(CHECKPOINT_FILE):
        ckpt = pd.read_csv(CHECKPOINT_FILE, encoding='utf-8-sig')
        # Lấy những id đã có address HOẶC đã có reviews
        done_ids = set(
            ckpt[
                ckpt['address'].notna() |
                ckpt['reviews'].notna()
            ]['restaurant_id'].tolist()
        )
        # Merge data từ checkpoint vào df
        for _, crow in ckpt.iterrows():
            rid = crow['restaurant_id']
            mask = df['restaurant_id'] == rid
            if crow.get('address'):
                df.loc[mask, 'address'] = crow['address']
            if crow.get('reviews'):
                df.loc[mask, 'reviews'] = crow['reviews']

        print(f"[RESUME] Đã có checkpoint: {len(done_ids)} nhà hàng")

    # --- Lọc nhà hàng cần cào ---
    need_crawl = df[
        ~df['restaurant_id'].isin(done_ids) &
        df['url'].notna()
    ].copy()

    print(f"[INFO] Cần cào address + reviews: {len(need_crawl)} nhà hàng")

    if len(need_crawl) == 0:
        print("[INFO] Tất cả đã có data rồi!")
        ordered_cols = [
            'restaurant_id', 'url', 'name', 'address',
            'latitude', 'longitude', 'rating', 'review_count',
            'reviews', 'price_range', 'category'
        ]
        for col in ordered_cols:
            if col not in df.columns:
                df[col] = ''
        df[ordered_cols].to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"[DONE] Đã lưu {OUTPUT_FILE}")
        return

    # --- Khởi động Selenium ---
    print(f"\n[BƯỚC 2] Cào address + reviews bằng Selenium...")
    driver = create_driver(headless=HEADLESS)

    success_addr  = 0
    success_rev   = 0
    fail_count    = 0

    try:
        for i, (idx, row) in enumerate(need_crawl.iterrows()):
            url  = str(row.get('url', ''))
            name = str(row.get('name', ''))[:40]

            print(f"\n   [{i+1}/{len(need_crawl)}] {name}")

            address, reviews = get_address_and_reviews(
                driver, url, max_reviews=MAX_REVIEWS
            )
            # --- Cào address ---
            if address:
                df.at[idx, 'address'] = address
                success_addr += 1
                print(f"      Address: {address[:60]}")
            else:
                print(f"      Address: ❌ Không lấy được")

            # --- Cào reviews ---
            if reviews:
                df.at[idx, 'reviews'] = json.dumps(
                    reviews, ensure_ascii=False
                )
                success_rev += 1
                print(f"      Reviews: {len(reviews)} reviews ✅")
            else:
                df.at[idx, 'reviews'] = json.dumps([])
                print(f"      Reviews: ❌ Không lấy được")

            if not address and len(reviews) == 0:
                fail_count += 1

            # --- Checkpoint mỗi 10 nhà hàng ---
            if (i + 1) % 10 == 0:
                ckpt_df = df[['restaurant_id', 'address',
                              'latitude', 'longitude', 'reviews']].copy()
                ckpt_df.to_csv(
                    CHECKPOINT_FILE, index=False, encoding='utf-8-sig'
                )
                print(f"   [CHECKPOINT] Đã lưu {i+1} nhà hàng")

            time.sleep(1)  # Tránh bị chặn

    except KeyboardInterrupt:
        print("\n[STOP] Người dùng dừng chương trình.")

    finally:
        driver.quit()

        # --- Checkpoint cuối ---
        ckpt_df = df[['restaurant_id', 'address',
                      'latitude', 'longitude', 'reviews']].copy()
        ckpt_df.to_csv(CHECKPOINT_FILE, index=False, encoding='utf-8-sig')

        # --- Lưu kết quả ---
        ordered_cols = [
            'restaurant_id', 'url', 'name', 'address',
            'latitude', 'longitude', 'rating', 'review_count',
            'reviews', 'price_range', 'category'
        ]
        for col in ordered_cols:
            if col not in df.columns:
                df[col] = ''

        df[ordered_cols].to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

        print(f"\n{'='*50}")
        print(f"[TỔNG KẾT]")
        print(f" - Tọa độ extract từ URL:  {coords_extracted}")
        print(f" - Address thành công:      {success_addr}")
        print(f" - Reviews thành công:      {success_rev}")
        print(f" - Thất bại hoàn toàn:      {fail_count}")
        print(f"-> Đã lưu {OUTPUT_FILE}")

if __name__ == "__main__":
    run()