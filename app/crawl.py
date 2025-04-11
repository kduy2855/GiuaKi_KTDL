import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

def crawl_sjc_gold_prices():
    url = 'https://sjc.com.vn/giavang/textContent.php'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    
    if response.status_code != 200:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'table'})

    if not table:
        print("Could not find the price table on the page.")
        return []

    data = []
    rows = table.find_all('tr')

    for row in rows[1:]:  # Skip header
        cols = row.find_all('td')
        if len(cols) < 3:
            continue
        
        location = cols[0].text.strip()
        buy_price = cols[1].text.strip().replace(',', '').replace('₫', '')
        sell_price = cols[2].text.strip().replace(',', '').replace('₫', '')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            buy_price = int(buy_price)
            sell_price = int(sell_price)
        except ValueError:
            continue  # Skip if price conversion fails

        data.append({
            'timestamp': timestamp,
            'location': location,
            'buy_price': buy_price,
            'sell_price': sell_price
        })

    return data

# Lưu dữ liệu vào file CSV
def save_to_csv(data, filename='sjc_gold_prices.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Saved {len(data)} rows to {filename}")

if __name__ == '__main__':
    gold_data = crawl_sjc_gold_prices()
    if gold_data:
        save_to_csv(gold_data)
