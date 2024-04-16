from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import pandas
import time


 
options = webdriver.ChromeOptions()
options.headless = True
driver = webdriver.Chrome(service=ChromeService(
    ChromeDriverManager().install()), options=options)


elem = driver.find_element(By.TAG_NAME, "html")
file_name = "lion.csv"
filename = "all3.txt"
# load target website



class writeCSV():
    def __init__(self):
        first = {"行程名稱":[],"時間":[],"價格":[],"入境機場":[],"出境機場":[],"天":[],"景點數":[],"日程":[],"自然旅遊景點":[],"文化旅遊景點":[],"遊樂園":[],"標籤":[],"網站":[]}
        self.file = pandas.DataFrame(first)
        # self.file = pandas.read_csv(file_name)

    def add_line(self, line):
        self.file.loc[len(self.file.index)] = line

    def toCsv(self):
        self.file.to_csv(file_name, index=False)

csvA = writeCSV()

# scroll to bottom of webpage
def scroll():
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    # wait for content to load
    #time.sleep(1)  


def getHref(url):
    driver.get(url)
    href = []
    for i in range(600):
        time.sleep(1)
        scroll()
    trips = driver.find_elements(By.CSS_SELECTOR, ".cardsList--2cG2D")
    print(len(trips))
    for t in trips:
        href.append(t.get_attribute('href'))
        write(t.get_attribute('href'), "web4")
    return href

def doOnce(url):
    try:
        driver.get(url)
        time.sleep(2)
        ###### title
        title = driver.find_element(By.CSS_SELECTOR, ".title--1dhv-")
        print(title.text, "title")

        ###### tags
        tags = driver.find_elements(By.CSS_SELECTOR, ".Style__TagSTY-zidxtd-0")
        tagsN = []
        for i in tags:
           tagsN.append(i.text)
        print(",".join(set(tagsN)))
        ###### price
        price = driver.find_element(By.CSS_SELECTOR, ".price--1fAWe span")
        print(price.text, "price")

        ###### date
        date = driver.find_elements(By.CSS_SELECTOR, ".Content0 .ContentColumn0")
        print(date[1].text, "date")

        ###### plane
        try:
            dep = driver.find_elements(By.CSS_SELECTOR, ".dep--2sC4s")
            arr = driver.find_elements(By.CSS_SELECTOR, ".arr--37QK7")
            print(dep, arr)
            to = dep[0].text + arr[0].text
            back = dep[1].text + arr[1].text
            print(to, back)
        except:
            to = None
            back = None

        
        try:
            ###### day schedule
            days = driver.find_elements(By.CSS_SELECTOR, ".daySchedule--objEr h3")
            for i in range(len(days)):
                land = False
                print(days[i].text)
                if "樂園" in days[i].text or "影城" in days[i].text:
                    land = True
                line = [title.text, date[1].text, price.text, to, back, len(days), len(days[i].text.split("~")), days[i].text, "", "", land, " ".join(set(tagsN)), url]
                csvA.add_line(line)
        
        except IndexError:
            pass
    except:
        pass

def write(line, filename):
    f = open(filename+".txt", "a", encoding="utf-8")
    f.write(line+"\n")
    f.close()

def main():
    # Japan and Korea
    url = "https://travel.liontravel.com/search?DepartureID=&ArriveID=--6,&GoDateStart=2024-03-16&GoDateEnd=2027-03-16&Keywords=&TravelType=0"
    getHref(url)
    # # Taiwan
    # url = "https://travel.liontravel.com/search?DepartureID=&ArriveID=--9,&GoDateStart=2024-03-16&GoDateEnd=2027-03-16&Keywords=&TravelType=0"
    # getHref(url)
    # # China
    # url = "https://travel.liontravel.com/search?DepartureID=&ArriveID=--5,&GoDateStart=2024-03-16&GoDateEnd=2027-03-16&Keywords=&TravelType=0"
    # getHref(url)
    # # South East
    # url = "https://travel.liontravel.com/search?DepartureID=&ArriveID=--7,&GoDateStart=2024-03-16&GoDateEnd=2027-03-16&Keywords=&TravelType=0"
    # getHref(url)
    # # Europe
    # url = "https://travel.liontravel.com/search?DepartureID=&ArriveID=--3,&GoDateStart=2024-03-16&GoDateEnd=2027-03-16&Keywords=&TravelType=0"
    # getHref(url)
    # # America
    # url = "https://travel.liontravel.com/search?DepartureID=&ArriveID=--1,&GoDateStart=2024-03-16&GoDateEnd=2027-03-16&Keywords=&TravelType=0"
    # getHref(url)
    # # Africa
    # url = "https://travel.liontravel.com/search?DepartureID=&ArriveID=--4,&GoDateStart=2024-03-16&GoDateEnd=2027-03-16&Keywords=&TravelType=0"
    # getHref(url)
    # # Australia
    # url = "https://travel.liontravel.com/search?DepartureID=&ArriveID=--2,&GoDateStart=2024-03-16&GoDateEnd=2027-03-16&Keywords=&TravelType=0"
    # getHref(url)


    # webs = pandas.read_csv(filename)
    # webs = webs.drop_duplicates()
    # webs.to_csv("all2.csv", index=False)

    # with open(filename) as webs:
    #     for url in webs:
    #         doOnce(url)
    #         csvA.toCsv()
    # csvA.toCsv()
    
    
if __name__ == "__main__":
    main()