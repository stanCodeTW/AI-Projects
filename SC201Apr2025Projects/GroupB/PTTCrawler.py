import aiohttp
import asyncio
import ssl
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
import os

# PTT URLs
BASE_URL = 'https://www.ptt.cc'
PTT_BOARD_URL = 'https://www.ptt.cc/bbs/{board}/index{page}.html'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Cookie': 'over18=1'
}

FINANCIAL_BOARDS = {
    'Stock': '股票討論',
    # 'Finance': '理財討論',
    # 'Fund': '基金投資',
    # 'Option': '選擇權',
    # 'Foreign_EX': '外匯',
}

START_DATE = datetime(2020, 1, 1)
END_DATE = datetime(2025, 12, 31)

SAVE_DIR = "volume/PTT"
os.makedirs(SAVE_DIR, exist_ok=True)

class PTTFetcher:
    def __init__(self, boards: dict, start_date: datetime, end_date: datetime):
        self.boards = boards
        self.start_date = start_date
        self.end_date = end_date
        self.session = None
        # 用來存放每天的資料
        self.daily_data = {}
        # 記錄已處理的日期（避免重複處理）
        self.processed_dates = set()
        # 記錄當前正在收集的日期
        self.current_collecting_dates = set()

    async def _fetch(self, url):
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            print(f"Fetch error for {url}: {e}")
            return None

    async def _get_latest_page(self, board: str):
        html = await self._fetch(PTT_BOARD_URL.format(board=board, page=''))
        if not html:
            return 1
            
        soup = BeautifulSoup(html, 'html.parser')
        btn = soup.select_one('div.btn-group-paging a.btn.wide:nth-of-type(2)')
        if btn and btn.get('href') and 'index' in btn['href']:
            match = re.findall(r'index(\d+)', btn['href'])
            if match:
                latest_index = int(match[0]) + 1
                return latest_index
        return 1

    def _extract_article_content(self, soup):
        """提取文章內容"""
        try:
            # 找到文章主要內容區域
            main_content = soup.find('div', {'id': 'main-content'})
            if not main_content:
                return "", [], ""
            
            # 移除不需要的元素
            for element in main_content.find_all(['div', 'span'], class_=['article-metaline', 'article-meta-tag', 'article-meta-value']):
                element.decompose()
            
            # 提取作者資訊
            author = ""
            metalines = soup.select('.article-metaline')
            for line in metalines:
                tag = line.select_one('.article-meta-tag')
                value = line.select_one('.article-meta-value')
                if tag and value and '作者' in tag.text:
                    author = value.text.strip()
                    break
            
            # 分離文章內容和推文
            content_text = main_content.get_text()
            
            # 找到推文開始的位置
            push_pattern = r'\n(推|→|噓)\s'
            push_match = re.search(push_pattern, content_text)
            
            if push_match:
                article_content = content_text[:push_match.start()].strip()
                push_section = content_text[push_match.start():].strip()
            else:
                article_content = content_text.strip()
                push_section = ""
            
            # 解析推文
            comments = []
            if push_section:
                push_lines = push_section.split('\n')
                for line in push_lines:
                    line = line.strip()
                    if line and re.match(r'^(推|→|噓)\s', line):
                        match = re.match(r'^(推|→|噓)\s+([^:]+):\s*(.+?)(\d{2}/\d{2}\s+\d{2}:\d{2})?$', line)
                        if match:
                            push_type = match.group(1)
                            user = match.group(2).strip()
                            comment = match.group(3).strip()
                            time_str = match.group(4) if match.group(4) else ""
                            
                            comments.append({
                                'type': push_type,
                                'user': user,
                                'comment': comment,
                                'time': time_str
                            })
            
            return article_content, comments, author
            
        except Exception as e:
            print(f"內容提取錯誤: {e}")
            return "", [], ""

    async def _parse_article(self, link: str, board: str):
        try:
            html = await self._fetch(BASE_URL + link)
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # 取得標題
            title_tag = soup.find('meta', {'property': 'og:title'})
            title = title_tag['content'].strip() if title_tag else ''

            # 取得時間和作者
            post_time = None
            author = ""
            
            metalines = soup.select('.article-metaline')
            for line in metalines:
                tag = line.select_one('.article-meta-tag')
                value = line.select_one('.article-meta-value')
                if tag and value:
                    if '作者' in tag.text:
                        author = value.text.strip()
                    elif '時間' in tag.text:
                        try:
                            time_str = value.text.strip()
                            post_time = datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y')
                        except:
                            continue
            
            if not post_time:
                date_spans = soup.select('.article-meta-value')
                if len(date_spans) >= 4:
                    try:
                        date_text = date_spans[3].text.strip()
                        post_time = datetime.strptime(date_text, '%a %b %d %H:%M:%S %Y')
                    except:
                        pass

            if not post_time:
                return None

            if post_time < self.start_date:
                return 'STOP'
            
            if post_time > self.end_date:
                return None

            # 提取文章內容和推文
            article_content, comments, extracted_author = self._extract_article_content(soup)
            
            if not author:
                author = extracted_author

            # 統計推文
            push_count = len([c for c in comments if c['type'] == '推'])
            boo_count = len([c for c in comments if c['type'] == '噓'])
            arrow_count = len([c for c in comments if c['type'] == '→'])
            
            return {
                'board': board,
                'title': title,
                'author': author,
                'datetime': post_time.isoformat(),
                'date': post_time.date().isoformat(),
                'year': post_time.year,
                'month': post_time.month,
                'day': post_time.day,
                'url': BASE_URL + link,
                'content': article_content,
                'content_length': len(article_content),
                'push_count': push_count,
                'boo_count': boo_count,
                'arrow_count': arrow_count,
                'total_comments': len(comments),
                'comments': comments
            }
        except Exception as e:
            print(f"文章解析錯誤 {link}: {e}")
            return None

    async def _parse_index_page(self, board: str, index: int):
        url = PTT_BOARD_URL.format(board=board, page=index)
        html = await self._fetch(url)
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        entries = soup.select('div.r-ent')

        links = []
        for entry in entries:
            a_tag = entry.select_one('div.title a')
            if a_tag and a_tag.get('href'):
                links.append(a_tag['href'])
        return links

    def _add_article_to_daily_data(self, data_item):
        """將文章加入對應日期的資料中"""
        date_str = data_item['date']
        
        if date_str not in self.daily_data:
            self.daily_data[date_str] = []
        
        self.daily_data[date_str].append(data_item)
        self.current_collecting_dates.add(date_str)

    def _save_completed_dates(self, current_page_dates):
        """檢查並儲存已完成的日期"""
        saved_count = 0
        dates_to_save = []
        
        # 找出不在當前頁面日期中的日期，表示該日期已經完成收集
        for date_str in list(self.current_collecting_dates):
            if date_str not in current_page_dates and date_str not in self.processed_dates:
                dates_to_save.append(date_str)
        
        # 儲存完成的日期
        for date_str in dates_to_save:
            if date_str in self.daily_data:
                json_filename = f"ptt_{date_str}.json"
                json_path = os.path.join(SAVE_DIR, json_filename)
                
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(self.daily_data[date_str], f, ensure_ascii=False, indent=2)
                    
                    article_count = len(self.daily_data[date_str])
                    print(f"💾 完成 {date_str}: {json_path} ({article_count} 篇)")
                    
                    # 清理已儲存的資料
                    del self.daily_data[date_str]
                    self.processed_dates.add(date_str)
                    self.current_collecting_dates.discard(date_str)
                    saved_count += 1
                    
                except Exception as e:
                    print(f"❌ 儲存失敗 {date_str}: {e}")
        
        return saved_count

    def _save_all_remaining_data(self):
        """儲存所有剩餘的日期資料"""
        saved_count = 0
        
        for date_str, articles in self.daily_data.items():
            if date_str not in self.processed_dates:
                json_filename = f"ptt_{date_str}.json"
                json_path = os.path.join(SAVE_DIR, json_filename)
                
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(articles, f, ensure_ascii=False, indent=2)
                    
                    print(f"💾 最終儲存 {date_str}: {json_path} ({len(articles)} 篇)")
                    saved_count += 1
                    
                except Exception as e:
                    print(f"❌ 最終儲存失敗 {date_str}: {e}")
        
        return saved_count

    async def _crawl_board(self, board: str, max_pages=100):
        print(f'\n🚀 開始抓取 {board} 板內容 (2025→2020)...')
        
        latest_page = await self._get_latest_page(board)
        print(f'{board} 最新頁碼：{latest_page}')

        page_count = 0
        total_articles = 0
        
        for index in range(latest_page, 0, -1):
            if max_pages and page_count >= max_pages:
                print(f"⚠️ {board} 已達最大頁數限制 ({max_pages} 頁)")
                break
                
            page_count += 1
            print(f"📄 處理 {board} 第 {index} 頁... (已獲取 {total_articles} 篇，第 {page_count} 頁)")
            
            links = await self._parse_index_page(board, index)
            if not links:
                continue

            # 記錄本頁面出現的日期
            current_page_dates = set()
            batch_size = 3
            should_stop = False
            
            for i in range(0, len(links), batch_size):
                batch_links = links[i:i+batch_size]
                tasks = [self._parse_article(link, board) for link in batch_links]
                results = await asyncio.gather(*tasks)
                
                for result in results:
                    if result == 'STOP':
                        print(f'🛑 {board} 抓到2020年以前的文章，停止抓取')
                        should_stop = True
                        break
                    elif result is not None:
                        self._add_article_to_daily_data(result)
                        current_page_dates.add(result['date'])
                        total_articles += 1
                
                if should_stop:
                    break
                
                await asyncio.sleep(1.0)
            
            # 檢查並儲存已完成的日期
            saved_count = self._save_completed_dates(current_page_dates)
            if saved_count > 0:
                print(f"✅ 本頁完成了 {saved_count} 個日期的儲存")
            
            if should_stop:
                break
                
        print(f'✅ {board} 板抓取完成，共處理 {page_count} 頁，獲得 {total_articles} 篇文章')
        return total_articles

    async def fetch_all(self, max_pages_per_board=100):
        # SSL 設定
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
            self.session = session
            
            print(f"📊 開始抓取 {len(self.boards)} 個板塊的完整內容")
            print(f"⏰ 時間範圍: 2025年 → 2020年1月1日")
            print(f"📁 儲存位置: {SAVE_DIR}")
            print("💾 按發文日期完成時自動儲存")
            print("📝 包含：標題、作者、內容、推文統計")
            print("📄 每天一個 JSON 檔案")
            print("-" * 50)
            
            total_all_articles = 0
            
            for i, board in enumerate(self.boards.keys(), 1):
                print(f"\n[{i}/{len(self.boards)}] 處理 {board} 板")
                
                try:
                    board_articles = await self._crawl_board(board, max_pages_per_board)
                    total_all_articles += board_articles
                    
                    print(f"✅ {board} 板完成！獲得 {board_articles} 篇資料")
                    print(f"📊 目前總計: {total_all_articles} 篇文章")
                    
                except Exception as e:
                    print(f"❌ {board} 板發生錯誤: {e}")
                    continue
                
                print("-" * 30)
            
            # 最終儲存所有剩餘的日期檔案
            print("\n🎯 執行最終儲存...")
            final_saved_files = self._save_all_remaining_data()
            
            print(f"\n🎉 全部完成！")
            print(f"📈 最終統計:")
            print(f"   總文章數: {total_all_articles}")
            print(f"   總處理日期: {len(self.processed_dates)}")
            
            if self.processed_dates:
                sorted_dates = sorted(self.processed_dates, reverse=True)
                print(f"   日期範圍: {min(sorted_dates)} ~ {max(sorted_dates)}")
            
            return total_all_articles

import nest_asyncio
nest_asyncio.apply()

async def main():
    print("🚀 開始執行 PTT 金融板爬蟲 - 按日期即時儲存版本 (2025→2020)...")
    print(f"📁 資料將儲存至: {SAVE_DIR}")
    print("📄 格式：每天一個 JSON 檔案 (ptt_YYYY-MM-DD.json)")
    print("💾 當天資料收集完成即儲存")
    
    fetcher = PTTFetcher(FINANCIAL_BOARDS, START_DATE, END_DATE)
    
    # 每板最多9000頁
    total_articles = await fetcher.fetch_all(max_pages_per_board=9000)
    
    return total_articles

# 執行
loop = asyncio.get_event_loop()
total_count = loop.run_until_complete(main())

print("\n✅ 程式執行完成！")
if total_count > 0:
    print(f"最終獲得 {total_count} 篇完整文章資料 (2020-2025年)")
    print("資料格式：每天一個 JSON 檔案，包含標題、作者、內容、推文統計、時間等")
    print(f"檔案位置: {SAVE_DIR}/ptt_YYYY-MM-DD.json")
else:
    print("沒有獲取到資料")