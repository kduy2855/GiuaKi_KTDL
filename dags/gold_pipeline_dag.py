from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import execute_values
import os

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def crawl_data(**context):
    url = 'https://sjc.com.vn/giavang/textContent.php'
    response = requests.get(url)
    response.encoding = 'utf-8'
    context['ti'].xcom_push(key='raw_html', value=response.text)

def transform_data(**context):
    html = context['ti'].xcom_pull(key='raw_html')
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'class': 'table'})
    rows = table.find_all('tr')[1:]  # Skip header
    data = []
    for row in rows:
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
    context['ti'].xcom_push(key='gold_data', value=data)

def save_data(**context):
    data = context['ti'].xcom_pull(key='gold_data')
    conn = psycopg2.connect(
        dbname='gold_db',
        user='myuser',
        password='mypassword',
        host='postgres',  # container name or IP
        port=5432
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
    cursor.close()
    conn.close()

with DAG(
    dag_id='gold_price_pipeline',
    default_args=default_args,
    description='Pipeline crawl + transform + save giá vàng SJC',
    schedule_interval='0 9 * * *',  # chạy 9h sáng mỗi ngày
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['gold', 'sjc', 'etl'],
) as dag:

    t1 = PythonOperator(
        task_id='crawl_gold',
        python_callable=crawl_data,
        provide_context=True
    )

    t2 = PythonOperator(
        task_id='transform_gold',
        python_callable=transform_data,
        provide_context=True
    )

    t3 = PythonOperator(
        task_id='save_gold',
        python_callable=save_data,
        provide_context=True
    )

    t1 >> t2 >> t3
