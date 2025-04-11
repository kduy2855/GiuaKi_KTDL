import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

def clean_sjc_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', {'class': 'table'})
    data = []
    rows = table.find_all('tr')
    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) >= 3:
            location = cols[0].get_text(strip=True)
            buy_price = cols[1].get_text(strip=True).replace(',', '').replace('₫', '')
            sell_price = cols[2].get_text(strip=True).replace(',', '').replace('₫', '')
            try:
                data.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'location': location,
                    'buy_price': int(buy_price),
                    'sell_price': int(sell_price)
                })
            except ValueError:
                continue
    return data

def save_to_postgresql(data):
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            host=os.environ['DB_HOST'],
            port=os.environ.get('DB_PORT', 5432)
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sjc_gold_prices (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                location TEXT NOT NULL,
                buy_price INTEGER NOT NULL,
                sell_price INTEGER NOT NULL
            );
        """)
        conn.commit()

        insert_query = """
            INSERT INTO sjc_gold_prices (timestamp, location, buy_price, sell_price)
            VALUES %s
        """
        values = [(d['timestamp'], d['location'], d['buy_price'], d['sell_price']) for d in data]
        execute_values(cursor, insert_query, values)
        conn.commit()
        print(f"Đã lưu {len(data)} dòng vào PostgreSQL.")
    except Exception as e:
        print(f"Lỗi khi ghi DB: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    url = 'https://sjc.com.vn/giavang/textContent.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    if res.status_code == 200:
        cleaned = clean_sjc_html(res.text)
        save_to_postgresql(cleaned)
    else:
        print("Không thể lấy dữ liệu SJC.")
