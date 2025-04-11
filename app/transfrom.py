from bs4 import BeautifulSoup
from datetime import datetime

def clean_sjc_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', {'class': 'table'})
    
    if not table:
        print("Không tìm thấy bảng dữ liệu.")
        return []

    rows = table.find_all('tr')
    data = []

    for row in rows[1:]:  # Bỏ hàng tiêu đề
        cols = row.find_all('td')
        if len(cols) >= 3:
            location = cols[0].get_text(strip=True)
            buy_price_raw = cols[1].get_text(strip=True)
            sell_price_raw = cols[2].get_text(strip=True)

            # Làm sạch giá (loại bỏ dấu phẩy, ký tự đặc biệt)
            buy_price = buy_price_raw.replace(',', '').replace('₫', '').strip()
            sell_price = sell_price_raw.replace(',', '').replace('₫', '').strip()

            try:
                buy_price = int(buy_price)
                sell_price = int(sell_price)
            except ValueError:
                continue  # Bỏ qua nếu giá không hợp lệ

            data.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'location': location,
                'buy_price': buy_price,
                'sell_price': sell_price
            })

    return data
