"""
Olist CSV 9개 → data/olist.sqlite 한 파일로 묶는 스크립트. (05_sql_olist 의 모든 SQL 이 이 DB 를 씀)

    python data/build_olist_sqlite.py

- 먼저 data/ 에 Kaggle "Brazilian E-Commerce Public Dataset by Olist" CSV 9개가 있어야 한다
  (받는 법은 data/download.py 의 OLIST 주석 참고).
- 테이블 이름을 짧게 바꾸고(orders, order_items ...), PRIMARY KEY / FOREIGN KEY 를 선언해서
  DBeaver 에서 ER 다이어그램이 그려지게 한다.
- geolocation 원본(100만 행)은 같은 우편번호 앞자리가 수십 번 반복되므로
  zip_code_prefix 하나당 한 행(평균 위경도 + 가장 많이 나온 도시)으로 줄인다 → 약 1.9만 행.
- 시각 열은 'YYYY-MM-DD HH:MM:SS' 문자열 그대로 둔다 (SQLite 의 date() / strftime() / julianday() 가 바로 읽음).
"""
import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "olist.sqlite"

SCHEMA = """
CREATE TABLE category_translation (
    product_category_name         TEXT PRIMARY KEY,
    product_category_name_english TEXT
);
CREATE TABLE customers (
    customer_id              TEXT PRIMARY KEY,   -- 주문마다 새로 발급되는 id
    customer_unique_id       TEXT NOT NULL,      -- 진짜 '사람' id (재구매 분석은 이것으로)
    customer_zip_code_prefix INTEGER,
    customer_city            TEXT,
    customer_state           TEXT
);
CREATE TABLE sellers (
    seller_id              TEXT PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city            TEXT,
    seller_state           TEXT
);
CREATE TABLE products (
    product_id                 TEXT PRIMARY KEY,
    product_category_name      TEXT REFERENCES category_translation(product_category_name),
    product_name_length        INTEGER,
    product_description_length INTEGER,
    product_photos_qty         INTEGER,
    product_weight_g           REAL,
    product_length_cm          REAL,
    product_height_cm          REAL,
    product_width_cm           REAL
);
CREATE TABLE orders (
    order_id                      TEXT PRIMARY KEY,
    customer_id                   TEXT NOT NULL REFERENCES customers(customer_id),
    order_status                  TEXT,
    order_purchase_timestamp      TEXT,
    order_approved_at             TEXT,
    order_delivered_carrier_date  TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT
);
CREATE TABLE order_items (
    order_id            TEXT NOT NULL REFERENCES orders(order_id),
    order_item_id       INTEGER NOT NULL,        -- 주문 안에서 1, 2, 3 ... (수량 = 최대값)
    product_id          TEXT REFERENCES products(product_id),
    seller_id           TEXT REFERENCES sellers(seller_id),
    shipping_limit_date TEXT,
    price               REAL,
    freight_value       REAL,
    PRIMARY KEY (order_id, order_item_id)
);
CREATE TABLE payments (
    order_id             TEXT NOT NULL REFERENCES orders(order_id),
    payment_sequential   INTEGER NOT NULL,       -- 한 주문을 여러 수단으로 나눠 낸 경우 1, 2, ...
    payment_type         TEXT,
    payment_installments INTEGER,
    payment_value        REAL,
    PRIMARY KEY (order_id, payment_sequential)
);
CREATE TABLE reviews (
    review_id               TEXT NOT NULL,       -- 원본에 같은 review_id 가 여러 주문에 붙은 경우가 있음
    order_id                TEXT NOT NULL REFERENCES orders(order_id),
    review_score            INTEGER,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TEXT,
    review_answer_timestamp TEXT,
    PRIMARY KEY (review_id, order_id)
);
CREATE TABLE geolocation (
    zip_code_prefix INTEGER PRIMARY KEY,
    lat             REAL,
    lng             REAL,
    city            TEXT,
    state           TEXT
);
CREATE INDEX idx_orders_customer   ON orders(customer_id);
CREATE INDEX idx_orders_purchase   ON orders(order_purchase_timestamp);
CREATE INDEX idx_customers_unique  ON customers(customer_unique_id);
CREATE INDEX idx_items_product     ON order_items(product_id);
CREATE INDEX idx_items_seller      ON order_items(seller_id);
CREATE INDEX idx_reviews_order     ON reviews(order_id);
"""

# 번역표에 빠져 있는 카테고리 2개 (products 에는 있음) → 직접 채워 FK 가 끊기지 않게 한다
MISSING_TRANSLATIONS = pd.DataFrame({
    "product_category_name": ["pc_gamer", "portateis_cozinha_e_preparadores_de_alimentos"],
    "product_category_name_english": ["pc_gamer", "kitchen_portables_and_food_preparators"],
})


def read(name):
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        raise SystemExit(f"{path.name} 가 없습니다. data/download.py 의 OLIST 안내대로 CSV 를 먼저 받으세요.")
    return pd.read_csv(path)


def build_geolocation():
    geo = read("olist_geolocation_dataset")
    geo.columns = ["zip_code_prefix", "lat", "lng", "city", "state"]
    coords = geo.groupby("zip_code_prefix")[["lat", "lng"]].mean().round(6)
    # 도시 이름은 같은 우편번호 안에서 가장 많이 나온 것으로
    counts = geo.groupby(["zip_code_prefix", "city", "state"]).size().reset_index(name="n")
    top_city = counts.sort_values("n").drop_duplicates("zip_code_prefix", keep="last")
    top_city = top_city.set_index("zip_code_prefix")[["city", "state"]]
    return coords.join(top_city).reset_index()


def main():
    translation = pd.concat([read("product_category_name_translation"), MISSING_TRANSLATIONS])
    products = read("olist_products_dataset").rename(columns={
        "product_name_lenght": "product_name_length",            # 원본 철자 오류 수정
        "product_description_lenght": "product_description_length",
    })
    tables = {
        "category_translation": translation,
        "customers": read("olist_customers_dataset"),
        "sellers": read("olist_sellers_dataset"),
        "products": products,
        "orders": read("olist_orders_dataset"),
        "order_items": read("olist_order_items_dataset"),
        "payments": read("olist_order_payments_dataset"),
        "reviews": read("olist_order_reviews_dataset"),
        "geolocation": build_geolocation(),
    }

    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    for name, df in tables.items():
        df.to_sql(name, conn, if_exists="append", index=False)
        print(f"{name:22s} {len(df):>9,} rows")
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    print(f"\n완료: {DB_PATH}  ({DB_PATH.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
