import requests
from bs4 import BeautifulSoup
import csv
import time

# Your login credentials
username = '請輸入你的帳號'
password = '請輸入你的密碼'

# Start a session
session = requests.Session()

headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

# Login URL and payload
login_url = 'https://www.mobile01.com/login.php'
login_payload = {
    'userid': username,
    'password': password,
    'submit': 'Login'
}

# Perform login
login_response = session.post(login_url, data=login_payload, headers=headers)

# Check if login was successful
if login_response.status_code == 200 and 'mobile01' in login_response.text:
    print("Login successful!")
else:
    print("Login failed!")
    exit()

profile_url = 'https://www.mobile01.com/userinfo.php'
profile_response = session.get(profile_url, headers=headers)
if '登入會員' not in profile_response.text:
    print("Session is valid!")
else:
    print("Session is not valid!")
    exit()

id_n = 0      # 爬下來文章的編號
page_number = 1     # mobile01 網頁頁數

# Create or open the CSV file
with open('scraped_articles.csv', mode='w', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)
    # Write the header row
    writer.writerow(['ID', 'URL', 'Title', 'Main Content', 'Replies Number', 'Replies1', 'Replies2'])

    while page_number <= 30:
        print(page_number)
        reply = []
        url = f"https://www.mobile01.com/topiclist.php?f=731&p={page_number}"
        res = session.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        current_page = soup.select_one('a.c-pagination__item.c-pagination__item--current')
        if page_number <= 30:
            article_title_html = soup.select('div[class="c-listTableTd__title"]')
        else:
            article_title_html = soup.select('div[class="c-listTableTd__title"]')
        article_title_reply = soup.select('div[class="o-fMini"]')

        print(f"URL: {url}")
        print("First few article titles on this page:")
        for each_article in article_title_html[:3]:
            print(each_article.a.text)

        if not article_title_html:
            print("No articles found, might have hit a pagination issue or session expired.")
            break

        for i in range(len(article_title_reply)):
            reply.append(article_title_reply[i].text)
        reply_num = 0      # 一頁裡面，第幾篇文章

        for each_article in article_title_html:
            # 篩選1頁裡文章是否符合我們要的標準的文章
            if any(keyword in each_article.a.text for keyword in ["風扇", "除濕", "空氣清淨", "全熱交換器",
                                                                  "循環扇", "空氣清靜", "空氣循環", "吊扇", "空氣濾網"]):
                reply_num += 1
                pass
            else:
                id_n += 1
                print("page=", page_number)
                print(f"ID: {id_n}")
                print(f"Title: {each_article.a.text}\n")
                content_page = int(reply[reply_num]) // 10 + 1  # 算回應有多少頁
                all_replies = []        # 所有回覆
                main_content = ""
                # 跑1篇文章裡，所有頁數的回覆
                for i in range(content_page):
                    article_url_w = f"https://www.mobile01.com/{each_article.a['href']}&p=1"
                    article_url = f"https://www.mobile01.com/{each_article.a['href']}&p={i + 1}"
                    print(f"Fetching article page: {article_url}")
                    article_text = each_article.a.text
                    article_res = requests.get(article_url, headers=headers)
                    article_soup = BeautifulSoup(article_res.text, 'html.parser')
                    # 跑主要文章
                    article_main = article_soup.select('div[itemprop="articleBody"]')
                    if article_main and i == 0:
                        main_content = article_main[0].text.strip()
                        print(f"Main Article Content: {main_content}")
                    # 跑回覆
                    article_content = article_soup.select('article[class="u-gapBottom--max c-articleLimit"]')
                    for j in range(len(article_content)):
                        article_content_text = article_content[j].text.strip()
                        if article_content_text:
                            print(f"Reply Content: {article_content_text}")
                            all_replies.append(article_content_text)
                    time.sleep(1)
                # 若回覆數量太多，需要分2格，不然輸出csv檔會有問題
                if content_page >= 20:
                    all_replies_w = all_replies[:200]
                    all_replies_w1 = all_replies[200:]
                    # Write data to CSV
                    writer.writerow([id_n, article_url_w, each_article.a.text, main_content, reply[reply_num],
                                     "\n".join(all_replies_w), "\n".join(all_replies_w1)])
                else:
                    writer.writerow([id_n, article_url_w, each_article.a.text, main_content, reply[reply_num],
                                     "\n".join(all_replies)])
                print("-" * 10)
                reply_num += 1
                time.sleep(1)
        page_number += 1
        time.sleep(1)
        # "\n".join(all_replies)
