import time
import json
import re
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ====== 1. 設定 ChromeOptions ======
chrome_options = Options()
# 以下兩行請根據你本機的路徑與 Profile 名稱調整
chrome_options.add_argument(r'--user-data-dir=/Users/changanlee/Library/Application Support/Google/Chrome')
chrome_options.add_argument('--profile-directory=Profile 2')

chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/111.0.0.0 Safari/537.36"
)

# ====== 2. 啟動瀏覽器 ======
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

# ====== 3. 讓使用者手動登入 Foodpanda ======
driver.get('https://www.foodpanda.com.tw/')
input("🔑 請在瀏覽器中手動登入 Foodpanda，完成驗證後輸入 'ok' 再繼續：")

# ====== 4. 從 CSV 檔讀取所有訂單編號 ======
order_ids = []
csv_file = "foodpanda_orders.csv"

with open(csv_file, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader, None)  # 跳過標題列（如果有的話）
    for row in reader:
        if len(row) > 1:  # 假設訂單編號在 row[1]
            order_ids.append(row[1].strip())

print(f"📋 找到 {len(order_ids)} 筆訂單，開始爬取...")

# 用來儲存「所有訂單」的完整資料 (for JSON)
all_orders_data = []

# 用來儲存「要寫入 CSV 的資料」：每個商品一行
csv_rows = []

# ====== 5. 逐一爬取每筆訂單 ======
for index, order_id in enumerate(order_ids, start=1):
    print(f"🔍 第 {index}/{len(order_ids)} 筆訂單: {order_id}")

    order_url = f'https://www.foodpanda.com.tw/new/orders/{order_id}'
    driver.get(order_url)
    time.sleep(5)  # 等待頁面載入

    # 檢查是否出現 reCAPTCHA，需要人工驗證
    try:
        captcha_wrapper = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, 'px-captcha-wrapper'))
        )
        input("⚠️ 發現 reCAPTCHA，請手動完成驗證後輸入 'ok' 再繼續：")
    except:
        pass

    # 建立一個字典來儲存該筆訂單的所有資訊
    # 這裡特別多加 "序號": index
    order_data = {
        "序號": index,
        "訂單編號": order_id,
        "商家名稱": "",
        "時間": "",
        "訂單": [],
        "小計": 0,
        "折扣": 0,
        "外送服務費": 0,
        "提袋/包材費": 0,
        "平台費": 0,
        "外送夥伴小費": 0,
        "總計(含稅)": 0
    }

    try:
        # ====== 5-1. 擷取商家名稱 & 時間 ======
        block1_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="past-order-details-page-root"]/div/div[2]/div/div/div[2]/div/div[1]'))
        )
        block1_text = block1_element.text.strip()

        block2_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="past-order-details-page-root"]/div/div[2]/div/div/div[3]/div/div[1]'))
        )
        block2_text = block2_element.text.strip()

        # 解析「商家名稱」與「時間」
        lines = block1_text.split("\n")
        order_data["商家名稱"] = lines[0]
        # 兼容「外送於」或「外帶自取於」
        order_data["時間"] = lines[1].replace("外送於", "").replace("外帶自取於", "").strip()

        # ====== 5-2. 解析「商品清單」與「各項費用」 ======
        order_lines = block2_text.split("\n")
        i = 0
        # --- 先用 while 迴圈抓取商品明細 ---
        while i < len(order_lines):
            # 檢查是否符合「1x」「2x」「3x」… 這種格式
            if re.match(r"(\d+)x$", order_lines[i]):
                quantity = int(order_lines[i][:-1])  # 把最後的 "x" 去掉，轉成整數
                i += 1
                if i >= len(order_lines):
                    break

                product_name = order_lines[i]
                i += 1

                # 收集商品細節（若有的話）
                details = []
                while i < len(order_lines) and not order_lines[i].startswith("$"):
                    details.append(order_lines[i])
                    i += 1

                # 接著應該遇到「$xxx」的價錢行
                if i < len(order_lines) and order_lines[i].startswith("$"):
                    price_str = order_lines[i].lstrip("$").strip()
                    price = int(re.sub(r"[^\d]", "", price_str))
                    order_data["訂單"].append({
                        "數量": quantity,
                        "商品": product_name,
                        "細節": ", ".join(details),
                        "價格": price
                    })
                    i += 1
            else:
                i += 1

        # --- 解析「小計 / 折扣 / 外送服務費 / 提袋/包材費 / 平台費 / 外送夥伴小費 / 總計(含稅)」 ---
        fee_labels = {
            "小計": "小計",
            "折扣": "折扣",
            "外送服務費": "外送服務費",
            "提袋/包材費": "提袋/包材費",
            "平台費": "平台費",
            "外送夥伴小費": "外送夥伴小費",
            "總計(含稅)": "總計 （含稅）"
        }
        for line in order_lines:
            for key, label in fee_labels.items():
                if label in line:
                    value = re.search(r"\$([-]?\d+)", line)
                    order_data[key] = int(value.group(1)) if value else 0

        # ====== 5-3. 存入 all_orders_data，並將每個商品展開成 csv_rows ======
        all_orders_data.append(order_data)

        # 為了 CSV，將同一筆訂單的所有商品「逐行」展開
        # 每行會包含「序號、訂單編號、商家名稱、時間、數量、商品、細節、價格、…」等
        for item in order_data["訂單"]:
            csv_rows.append([
                index,  # <--- 新增「序號」
                order_data["訂單編號"],
                order_data["商家名稱"],
                order_data["時間"],
                item["數量"],
                item["商品"],
                item["細節"],
                item["價格"],
                order_data["小計"],
                order_data["折扣"],
                order_data["外送服務費"],
                order_data["提袋/包材費"],
                order_data["平台費"],
                order_data["外送夥伴小費"],
                order_data["總計(含稅)"]
            ])

    except Exception as e:
        print(f"⚠️ 訂單 {order_id} 擷取失敗: {e}")

# ====== 6. 儲存為 JSON 檔 ======
json_file = "foodpanda_orders_details.json"
with open(json_file, "w", encoding="utf-8") as file:
    json.dump(all_orders_data, file, indent=4, ensure_ascii=False)

print(f"📁 所有訂單詳細資料已儲存至 {json_file}")

# ====== 7. 儲存為 CSV 檔 ======
csv_output_file = "foodpanda_orders_details.csv"
with open(csv_output_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # 在這裡加上「序號」欄位
    writer.writerow([
        "序號", "訂單編號", "商家名稱", "時間",
        "數量", "商品", "細節", "價格",
        "小計", "折扣", "外送服務費", "提袋/包材費",
        "平台費", "外送夥伴小費", "總計(含稅)"
    ])
    writer.writerows(csv_rows)

print(f"📁 所有訂單詳細資料已儲存至 {csv_output_file}")

# ====== 8. 關閉瀏覽器 ======
driver.quit()
