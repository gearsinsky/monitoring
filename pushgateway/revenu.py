from datetime import datetime
import requests
from dotenv import load_dotenv
import os

# 加載 .env 檔案中的環境變數
load_dotenv(dotenv_path="/home/ubuntu/books/.env")

# 讀取環境變數
woocommerce_key = os.getenv("CONSUMER_KEY")
woocommerce_secret = os.getenv("CONSUMER_SECRET")
pushgateway_url = os.getenv("PUSHGATEWAY_URL")  # Prometheus Pushgateway URL

if not woocommerce_key or not woocommerce_secret:
    raise ValueError("無法從環境變數中讀取 CONSUMER_KEY 或 CONSUMER_SECRET")
if not pushgateway_url:
    raise ValueError("無法從環境變數中讀取 PUSHGATEWAY_URL")

# WooCommerce API 設定
API_URL = "https://www.rising-shop-dg.com/wp-json/wc/v3/orders"

def get_orders_total_by_period(start_date, end_date):
    """
    根據指定時間範圍查詢 WooCommerce 訂單總金額（不篩選狀態）
    """
    params = {
        "consumer_key": woocommerce_key,
        "consumer_secret": woocommerce_secret,
        "after": start_date,
        "before": end_date,
        "per_page": 100  # 一次最多取回 100 筆
    }

    total_amount = 0.0
    page = 1

    while True:
        params["page"] = page
        response = requests.get(API_URL, params=params)

        if response.status_code != 200:
            raise Exception(f"API 請求失敗: {response.status_code} - {response.text}")

        orders = response.json()
        if not orders:
            break

        for order in orders:
            total_amount += float(order["total"])

        page += 1

    return total_amount

def push_to_prometheus(metric_name, value, labels=None):
    labels_str = ""
    if labels:
        labels_str = ",".join([f'{key}="{value}"' for key, value in labels.items()])
    
    data = f"{metric_name}{{{labels_str}}} {value}\n" 
    print(f"推送的數據: {data}")
    
    url = f"{pushgateway_url}/metrics/job/woocommerce"
    headers = {"Content-Type": "text/plain"}
    response = requests.put(url, data=data, headers=headers)

    if response.status_code not in [200, 202]:
        raise Exception(f"Pushgateway 請求失敗: {response.status_code} - {response.text}")

if __name__ == "__main__":
    now = datetime.now()
    year, month = now.year, now.month

    try:
        # 計算當月營收
        month_start = f"{year}-{month:02d}-01T00:00:00"
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        month_end = f"{next_year}-{next_month:02d}-01T00:00:00"
        monthly_revenue = get_orders_total_by_period(month_start, month_end)

        print(f"{year} 年 {month} 月的 WooCommerce 訂單總金額為: ${monthly_revenue:.2f}")
        push_to_prometheus("woocommerce_monthly_revenue", monthly_revenue, {"year": year, "month": month})
        
        # 計算當年營收
        year_start = f"{year}-01-01T00:00:00"
        year_end = f"{year+1}-01-01T00:00:00"
        yearly_revenue = get_orders_total_by_period(year_start, year_end)

        print(f"{year} 年的 WooCommerce 訂單總金額為: ${yearly_revenue:.2f}")
        push_to_prometheus("woocommerce_year_revenue", yearly_revenue, {"year": year})
        
        print("成功將數據傳送到 Prometheus Pushgateway")
    except Exception as e:
        print(f"操作失敗: {e}")

