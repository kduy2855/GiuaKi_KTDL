import psycopg2
from psycopg2.extras import execute_values

def save_to_postgresql(data, db_config):
    """
    data: list các dict đã được clean
    db_config: dict chứa thông tin kết nối DB
    """
    try:
        conn = psycopg2.connect(
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config.get('port', 5432)
        )
        cursor = conn.cursor()

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS sjc_gold_prices (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            location TEXT NOT NULL,
            buy_price INTEGER NOT NULL,
            sell_price INTEGER NOT NULL
        );
        """
        cursor.execute(create_table_sql)
        conn.commit()

        insert_query = """
        INSERT INTO sjc_gold_prices (timestamp, location, buy_price, sell_price)
        VALUES %s
        """

        values = [
            (item['timestamp'], item['location'], item['buy_price'], item['sell_price'])
            for item in data
        ]

        execute_values(cursor, insert_query, values)
        conn.commit()
        print(f"Đã lưu {len(data)} dòng vào PostgreSQL.")

    except Exception as e:
        print(f"Lỗi kết nối hoặc ghi DB: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()
