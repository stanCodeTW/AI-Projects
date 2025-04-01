from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

# 1. 設定 ChromeOptions
chrome_options = Options()

# 指定 Chrome 使用者資料路徑 (確保已登入)
chrome_options.add_argument(
    r'--user-data-dir=/Users/changanlee/Library/Application Support/Google/Chrome'
)
chrome_options.add_argument('--profile-directory=Profile 2')  # 使用指定的 Chrome Profile

# 其他選項，避免被檢測為自動化
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/111.0.0.0 Safari/537.36"
)

# 2. 啟動瀏覽器
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 3. **讓使用者手動登入 Foodpanda**
url_login = 'https://www.foodpanda.com.tw/'  # 這是首頁，讓使用者手動登入
driver.get(url_login)
print("🔑 請在瀏覽器中手動登入 Foodpanda，完成驗證後輸入 'ok' 再繼續...")
input("👉 請輸入 'ok' 後按 Enter：")

# 4. **開啟 Foodpanda 訂單頁面**
url_orders = 'https://www.foodpanda.com.tw/new/orders'
driver.get(url_orders)
print("✅ 成功登入，開始爬取訂單資料...")
time.sleep(5)  # 等待頁面加載

# 5. 滾動至特定元素，觸發新內容載入
def scroll_to_load_more(driver, max_attempts=30, delay=2):
    attempts = 0
    last_order_count = 0  # 記錄訂單數量
    while attempts < max_attempts:
        try:
            # 找到觸發加載的元素
            load_trigger_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="reorder-page-root"]/div/div[3]/div/footer/div[1]/div/div/div[1]/div[1]/h4/a'))
            )
            # 滾動到該元素
            driver.execute_script("arguments[0].scrollIntoView();", load_trigger_element)
            time.sleep(delay)  # 等待新內容加載
        except Exception:
            print("⚠️ 無法找到觸發載入的元素，可能已加載完畢")
            break
        
        # 確認是否有新訂單載入
        orders = driver.find_elements(By.XPATH, '//*[@id="reorder-page-root"]/div/div[2]/div/div/div/div[2]/div')
        if len(orders) == last_order_count:
            print("✅ 沒有新的訂單載入，停止滾動")
            break  # 如果訂單數量沒有變化，代表載入完畢
        last_order_count = len(orders)
        attempts += 1

scroll_to_load_more(driver)

# 6. 擷取所有訂單資訊
orders = driver.find_elements(By.XPATH, '//*[@id="reorder-page-root"]/div/div[2]/div/div/div/div[2]/div')

data_list = []
for order in orders:
    try:
        # 擷取商家名稱
        restaurant_name = order.find_element(By.XPATH, './/div/div[2]/div[1]').text.strip()
        # 擷取訂單細節（移除 "Order #"）
        order_details_raw = order.find_element(By.XPATH, './/div/div[2]/div[2]/div[2]').text.strip()
        order_details = order_details_raw.replace("Order #", "").strip()  # 移除 "Order #"，保留訂單號碼
        
        data_list.append([restaurant_name, order_details])
    except Exception as e:
        # print(f"⚠️ 擷取訂單資訊時發生錯誤: {e}")
        continue

# 7. 儲存為 CSV 檔案
output_file = "foodpanda_orders.csv"
with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["商家名稱", "訂單編號"])  # 欄位名稱
    writer.writerows(data_list)  # 寫入所有訂單資料

print(f"✅ 訂單資料已儲存至 {output_file}")

# 8. 關閉瀏覽器
driver.quit()
