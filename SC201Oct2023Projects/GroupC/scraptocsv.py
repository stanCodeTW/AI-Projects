from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import pandas
import time, csv


 
options = webdriver.ChromeOptions()
options.headless = True
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)


elem = driver.find_element(By.TAG_NAME, "html")

name = "bird"


# load target website
url = 'https://www.besttour.com.tw/e_web/search-group?v=/////////////'


# get website content
driver.get(url)


class tocsv():
    def __init__(self):
        self.panda = pandas.DataFrame({"行程名稱":[], "價格":[], "入境機場(看day1)":[], "出境機場(看最後一天)":[], "天":[], "景點數":[], "日程":[], "自然旅遊景點":[], "文化旅遊景點":[], "遊樂園":[], "對象(安琪)":[], "景點類別(安琪)":[]})
        self.leng = 0

    def add_line(self, line):
        print(line)
        a = pandas.DataFrame(line)
        print(a)
        self.panda.append(line, ignore_index=True)

    def nexttrip(self):
        self.leng+=1

    def output(self):
        print(self.panda)
        self.panda.to_csv("trip.csv")


s = tocsv()
# scroll to bottom of webpage
def scroll():
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    # wait for content to load
    time.sleep(20)
      


def getHref():
    trips = driver.find_elements(By.CSS_SELECTOR, ".TD > a")
    print(len(trips))
    href = []
    for t in trips:
        # print(t.get_attribute('href'))
        # print(t.get_attribute('title'))
        href.append(t.get_attribute('href'))
        write(t.get_attribute('href'), "web")
    return href

def doOnce(url, num):
    time.sleep(0.1)
    airport = []
    try:
        ret=[]
        ###### title
        driver.get(url)
        title = driver.find_elements(By.CSS_SELECTOR, "#travel_detail_info_title2 span")
        title = title[1].text
        ###### price
        price = driver.find_element(By.CSS_SELECTOR, ".TB_B_price div span")
        price = price.text

        ###### date
        date = driver.find_elements(By.CSS_SELECTOR, "#travel_detail_info_date div")
        date = date[0].text+date[1].text

        ###### day schedule
        try:
            
            for i in range(15):
                days = driver.find_elements(By.CSS_SELECTOR, "#travel_detail_schedule_day"+str(i)+" div")
                Dtitle = days[0].find_elements(By.CSS_SELECTOR, "div")
                day_title = Dtitle[1].text, num
                places = driver.find_elements(By.CSS_SELECTOR, "#travel_detail_schedule_day"+str(i)+" .travel_detail_schedule_all .txt")
                a = 1
                land = False
                for k in places[1:]:
                    c = k.find_elements(By.CSS_SELECTOR, "span")
                    schedule = c[0].text
                    if "/" in schedule or "✈"in schedule:
                        airport.append(schedule)
                    a+=1
                    if "樂園" in schedule or "影城" in schedule:
                        land = True
                
                ret.append([title, date, price, "", "", i, len(places)-1, day_title[0], "", "", land, "", ""])
        except IndexError:
            pass
    except:
        pass
    if len(airport)==2:
        for i in range(len(ret)):
            ret[i][3] = airport[0]
            ret[i][4] = airport[1]
    return ret

def write(line, filename):
    f = open(filename+".txt", "a", encoding="utf-8")
    f.write(line+"\n")
    f.close()




def main():
    scroll()
    href = getHref()
    i=0
    with open("travel.csv", "w", encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["行程名稱","時間", "價格", "入境機場(看day1)", "出境機場(看最後一天)", "天", "景點數", "日程", "自然旅遊景點", "文化旅遊景點", "遊樂園", "對象(安琪)", "景點類別(安琪)"])
        for url in href:
            i+=1
            for c in doOnce(url, str(i)):
                writer.writerow(c)
        
    
if __name__ == "__main__":
    main()