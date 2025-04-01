import requests
import openrouteservice
import time
from geopy.distance import geodesic
from tqdm import tqdm
import json
import os
import pandas as pd
from collections import defaultdict
from datetime import datetime
import openai
from openai import OpenAI
import gradio as gr
import chromadb
from chromadb import PersistentClient
from pathlib import Path

# --------------------- API 金鑰設定 ---------------------#
os.environ[
    "OPENAI_API_KEY"] = 'YOUR_OPENAI_API_KEY'  # 替換為你的 API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

API = 'AIzaSyAbeUNGBay9f8K1k46hNIbKIvumHZVjGgc'  # Google Maps API Key
OR_API_KEY = "5b3ce3597851110001cf6248935e4404f78c443fbec30b30ca472277"  # OpenRouteService API Key

# --------------------- 地址 Alias 與快取設定 ---------------------#
# 地址 alias 對應，讓你可以以簡稱輸入，並轉換成完整地址
ADDRESS_ALIAS = {
    "住家": "台北市信義區松山路123號"
}


# 若輸入的地址在 alias 中，則以 alias 所對應的實際地址作為搜尋依據
def get_real_address(address):
    return ADDRESS_ALIAS.get(address.strip(), address.strip())


# 快取資料存放資料夾（會自動建立）
CACHE_FOLDER = Path("./restaurant_cache")
CACHE_FOLDER.mkdir(exist_ok=True)


def get_cache_filename(address):
    safe_name = address.replace(" ", "_")
    return CACHE_FOLDER / f"restaurant_cache_{safe_name}.json"


def load_restaurants_cache(address):
    cache_file = get_cache_filename(address)
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_restaurants_cache(address, restaurants):
    cache_file = get_cache_filename(address)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)


# --------------------- Embedding + Parquet 快取 ---------------------#
csv_path = './labeled_history_dataset.csv'
parquet_path = './label_vectors_with_weight.parquet'


def calculate_weight(row, half_life_months=3):
    now = datetime.now()
    count_score = min(row['count'] / 10, 1.0)
    recency_months = (now - pd.to_datetime(row['latest_date'])).days / 30
    recency_score = 0.5 ** (recency_months / half_life_months)
    return round((count_score + recency_score) / 2, 4)


def get_label_embedding(label):
    response = client.embeddings.create(
        input=label,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


if os.path.exists(parquet_path):
    print("🟢 已找到 parquet 檔案，直接載入已計算好的 embedding！")
    label_stats = pd.read_parquet(parquet_path)
else:
    print("🔄 找不到 parquet，從 CSV 建立 embedding...")
    df = pd.read_csv(csv_path)
    df_exploded = df.assign(label=df['labels'].str.split(',')).explode('label')
    df_exploded['label'] = df_exploded['label'].str.strip()
    label_stats = df_exploded.groupby('label').agg(
        count=('label', 'count'),
        latest_date=('Date', 'max')
    ).reset_index()
    label_stats['weight'] = label_stats.apply(calculate_weight, axis=1)
    embeddings = []
    for label in tqdm(label_stats['label'].tolist(), desc="Embedding"):
        embeddings.append(get_label_embedding(label))
    label_stats['embedding'] = embeddings
    label_stats.to_parquet(parquet_path, index=False)
    print("✅ 已儲存 embedding 至 parquet！")

# --------------------- 建立或重建 Chroma 資料庫 ---------------------#
chroma_path = './chroma_db'
chroma_client = PersistentClient(path=chroma_path)
collection = chroma_client.get_or_create_collection("label_vectors_with_count_and_date")

if collection.count() > 0:
    all_data = collection.get()
    collection.delete(ids=all_data['ids'])
    print("🧹 已清空原有資料")

for i, row in tqdm(label_stats.iterrows(), total=len(label_stats)):
    collection.add(
        ids=[f"label_{i}"],
        documents=[row['label']],
        embeddings=[row['embedding']],
        metadatas=[{
            'label': row['label'],
            'count': row['count'],
            'latest_date': str(row['latest_date']),
            'weight': row['weight']
        }]
    )
print(f"✅ Chroma collection 完成，共 {collection.count()} 筆資料")


# --------------------- 輔助函式 ---------------------#
def together(num, minutes):
    if num == 1:
        return 'walking', 'foot-walking', minutes
    return 'driving', 'driving-car', minutes


def transform(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API}"
    data = requests.get(url).json()
    if data.get('status') == 'OK':
        loc = data['results'][0]['geometry']['location']
        return loc['lat'], loc['lng']
    return None, None


def get_isochrone(lat, lng, profile, range_time):
    client_or = openrouteservice.Client(key=OR_API_KEY)
    location = [lng, lat]
    iso = client_or.isochrones(locations=[location], profile=profile, range=[range_time])

    def get_max_distances(origin, iso):
        dists = []
        for f in iso['features']:
            max_d = max(
                geodesic((origin[1], origin[0]), (pt[1], pt[0])).m
                for poly in f['geometry']['coordinates'] for pt in poly
            )
            dists.append(max_d)
        return dists

    return iso, get_max_distances(location, iso)


def search_nearby(lat, lng, radius):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=restaurant&key={API}"
    restaurants = []
    while url:
        res = requests.get(url).json()
        if res.get('status') == 'OK':
            for r in res['results']:
                restaurants.append({
                    'name': r.get('name'),
                    'address': r.get('vicinity'),
                    'place_id': r.get('place_id'),
                    'rating': r.get('rating', 0),
                    'types': r.get('types'),
                    'price_level': r.get('price_level', '未知')
                })
            token = res.get("next_page_token")
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken={token}&key={API}" if token else None
            if token: time.sleep(2)
        else:
            break
    return restaurants


def find_restaurant(lat, lng, minutes, mode, radius):
    radius = radius[0]
    restaurants = search_nearby(lat, lng, radius)
    while len(restaurants) < 50 and radius < 20000:
        radius = int(radius * 1.2)
        restaurants = search_nearby(lat, lng, radius)
    return sorted(restaurants, key=lambda x: x['rating'], reverse=True)


def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


def openai_api(system_msg, user_msg):
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        temperature=0.7
    )
    return res.choices[0].message.content


def combine_input_to_sentence(address, mode, minutes, user_prompt):
    mode_dict = {1: "步行", 2: "開車", 3: "外送"}
    return f"我在 {address}，希望在 {minutes} 分鐘以內，透過 {mode_dict.get(mode, '行動')} 可以找到的推薦。使用者額外需求：{user_prompt}"


# --------------------- Gradio 主程式 ---------------------#
def gradio_app(address, mode, minutes, user_request, force_refresh=False):
    """
    使用者輸入地址，獲取最新的餐廳資訊，並結合過去的用餐記錄與權重加權後的 RAG 來推薦。
    若地址屬於固定地址（例如「住家」），則優先讀取快取檔，否則即時搜尋。
    """
    try:
        mode_int = int(mode)
        minutes = int(minutes)
    except:
        return "❌ 請確認模式與分鐘數格式正確。"

    # 取得實際地址（若有 alias 則轉換）
    real_address = get_real_address(address)

    mode_val, profile, minutes_val = together(mode_int, minutes)
    text = combine_input_to_sentence(real_address, mode_int, minutes, user_request)
    text_embedding = get_embedding(text)

    # 查詢向量資料庫，取得 metadatas（含 weight）
    results = collection.query(
        query_embeddings=[text_embedding],
        n_results=50,
        include=['documents', 'distances', 'metadatas']
    )
    ranked_results = []
    for doc, dist, meta in zip(results["documents"][0], results["distances"][0], results["metadatas"][0]):
        weight = meta.get('weight')
        score = (1 - dist) * weight
        ranked_results.append((doc, score))
    ranked_results.sort(key=lambda x: x[1], reverse=True)
    top_context = "\n".join([doc for doc, _ in ranked_results[:15]])

    # 地址轉經緯度
    lat, lng = transform(real_address)
    if lat is None or lng is None:
        return "無法取得該地址的經緯度，請確認地址是否正確。"

    # 取得等時線資訊
    _, max_dists = get_isochrone(lat, lng, profile, minutes_val * 60)

    # 若為固定地址（例如「住家」）且未強制刷新，則優先讀取快取
    fixed_address = "住家"  # 這裡可以修改成你的固定地址或 alias
    if real_address == ADDRESS_ALIAS.get("住家", "住家") and not force_refresh:
        cached_restaurants = load_restaurants_cache("住家")
        if cached_restaurants is not None:
            restaurants = cached_restaurants
            print("✅ 使用快取的餐廳結果")
        else:
            print("🚀 快取不存在，執行即時搜尋...")
            restaurants = find_restaurant(lat, lng, minutes_val, mode_val, max_dists)
            save_restaurants_cache("住家", restaurants)
    else:
        print("🔍 即時搜尋餐廳中...")
        restaurants = find_restaurant(lat, lng, minutes_val, mode_val, max_dists)

    print(f"找到 {len(restaurants)} 間餐廳")
    system_message = f"""
    你是一個專業的餐廳推薦 AI 助理，你的目標是根據使用者目前位置、過往消費偏好、RAG 檢索結果以及使用者當前需求，推薦最適合的餐廳。

    # 💡 **規則**
    1. 以下是最新的餐廳清單（restaurants），只能從這份清單中推薦。

    2. 當使用者有特定品項需求（{user_request}），請**優先推薦**：
       - 餐廳菜單或描述中包含此品項或其同義詞的餐廳。
       - 若沒有完全匹配，請推薦「高度相近類別」的餐廳，並在推薦理由中解釋相似性。

    3. 同時參考下方 RAG 檢索結果（過往紀錄標籤）進行輔助說明：
       - 如果推薦餐廳的菜色、風格或類別與 RAG 標籤高度匹配，請列出：
         - 相符標籤
         - 標籤在歷史紀錄中的出現頻率描述（「經常出現」、「近期多次出現」等）
         - 為什麼此標籤讓這間餐廳值得推薦
       - 如果只是「相似」而非完全匹配，也請標註「參考了相似標籤」並解釋

    4. 請對每一間推薦餐廳，輸出以下資訊：
       - 餐廳名稱
       - 推薦原因（說明與使用者需求、標籤的關聯或相似性，至少 2-3 句話）
       - 預估價格範圍（若清單中有提供）
       - 過往紀錄參考（列出標籤與頻率描述，若無直接匹配則寫「參考相似標籤」）

    5. 若沒有找到與需求完全匹配的餐廳，請使用「相近餐廳推薦」，並清楚標示「相近原因」
    6. 如果連相近推薦也無法提供，請回覆：「目前沒有在指定範圍內找到符合『{user_request}』或相近類型的餐廳，建議您考慮更多元的選擇。」
    7. 不要虛構餐廳或標籤，只能使用清單與 context 中提供的資訊。
    8. 請用條列式、清楚格式化方式輸出，每間餐廳分段列出資訊。

    ---

    # ✅ 使用者輸入需求：
    「{user_request}」

    # ✅ 以下為 RAG 檢索結果（使用者過往紀錄標籤，含權重、頻率與日期參考）：
    {top_context}

    # ✅ 以下為最新可推薦餐廳清單（僅能從下方餐廳清單選擇）：
    {json.dumps(restaurants, ensure_ascii=False, indent=2)}

    請綜合參考上述資訊，推薦 3 間餐廳，並針對每一間餐廳詳細說明推薦原因、價格範圍，以及與過往偏好標籤或需求的關聯性。
    """
    ans = openai_api(system_message, user_request)
    return ans


# --------------------- 建立 Gradio 介面 ---------------------#
gr.close_all()
iface = gr.Interface(
    fn=gradio_app,
    inputs=[
        gr.Textbox(label="地點"),
        gr.Radio(choices=["1", "2", "3"], label="模式", value="1"),
        gr.Number(label="所需最小時間", value=10),
        gr.Textbox(label="請輸入您的請求"),
        gr.Checkbox(label="手動刷新", value=False)
    ],
    outputs="text",
    title="餐點推薦 Chatbot",
    cache_examples=False
)
iface.launch(debug=True, share=False)