import psycopg2
import pandas as pd

# Kết nối đến PostgreSQL
conn = psycopg2.connect(
    dbname="Web-Ecommere",
    user="postgres",
    password="duc8504@@",
    host="localhost",
    port="5432"
)

# Tạo một cursor
cur = conn.cursor()

# Truy vấn danh sách các bảng trong schema "public"
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
""")

# Lấy danh sách bảng
tables = cur.fetchall()
print("Danh sách các bảng:", [table[0] for table in tables])


# Query lấy dữ liệu
query = """
SELECT pv.*, c.name AS category_name
FROM product_variant pv
JOIN products p ON pv.product_id = p.id
JOIN category c ON p.category_id = c.id;
"""

# Đọc dữ liệu vào DataFrame
df = pd.read_sql(query, conn)

# Lưu thành CSV
df.to_csv("product_variant_with_category.csv", index=False, encoding="utf-8")

# Đóng kết nối
conn.close()


# Đóng kết nối
cur.close()
conn.close()