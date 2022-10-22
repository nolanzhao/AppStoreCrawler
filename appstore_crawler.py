import os
import time
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
import platform
import json
import pandas as pd
from bs4 import BeautifulSoup
import random
import re
from traceback import format_exc
from config import *



def save_data(content, filename):
    if filename == "res.json":
        filepath = f"./result/{filename}"
    else:
        if filename.endswith(".json"):
            filepath = f"./data/{filename}"
        else:
            filepath = f"./page/{filename}"
    with open(filepath, "w") as f:
        f.write(content)


def gen_excel():
    res = []
    for filepath in os.listdir("./data"):
        with open(f"./data/{filepath}", 'r') as f:
            data = json.load(f)
            ##################################################
            data["rating"] = data["detail"]["rating"]
            data["description"] = data["detail"]["description"]
            del data["detail"]
            ##################################################
            res.append(data)
    df = pd.DataFrame(res)
    df["rank"] = df["rank"].astype(int)
    df = df.sort_values(by='rank', ascending=True)
    df.to_excel("result/res.xlsx", index=False)


def gen_json():
    res = []
    for filepath in os.listdir("./data"):
        with open(f"./result/{filepath}", 'r') as f:
            data = json.load(f)
            res.append(data)
    res = sorted(res, key=lambda x: int(x["rank"]))
    json_data = json.dumps(res, ensure_ascii=False, indent=4)
    save_data(json_data, "res.json")


def get_driver():
    current_platform = platform.system()
    driver = None
    if current_platform == 'Darwin':
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--disable-gpu')
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)
        time.sleep(0.5)
    if current_platform == 'Linux':
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.set_page_load_timeout(60)
        time.sleep(0.5)
    return driver


def retrive_apps(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    save_data(soup.prettify(), "top100.html")

    items = soup.find_all(
        "li", class_="l-column--grid small-valign-top we-lockup--in-app-shelf l-column small-6 medium-3 large-2")
    apps = []
    for li in items:
        a = li.find("a")
        url = a.get("href")
        text = a.get_text()

        s = [i for i in text.split("\n") if i.replace(" ", "") != ""]
        rank, name, company = s[0], s[1], s[2].strip()
        print(rank, name, company, url)
        apps.append({"rank": rank, "name": name, "company": company, "url": url})
    return apps


def retrive_detail(page_source, rank):
    soup = BeautifulSoup(page_source, 'html.parser')
    save_data(soup.prettify(), f"app_{rank}.html")

    desc_item = soup.select('div[class*="we-truncate we-truncate--multi-line we-truncate--interactive"]')[0]
    # print(desc_item.get_text())
    rating_item = soup.find("span", class_="we-customer-ratings__averages__display")
    # print(rating_item.get_text())
    return {"description": desc_item.get_text(), "rating": rating_item.get_text()}


def get_rand_num():
    return random.randint(30, 60) / 10.0


def main(BASE_URL=None, START_INDEX=None):
    print("TASK BEGIN.")
    try:
        index_url = BASE_URL
        driver = get_driver()
        driver.get(index_url)
        driver.implicitly_wait(1)
        time.sleep(1)

        apps = retrive_apps(driver.page_source)

        for item in apps[START_INDEX - 1:]:
            rank = item["rank"]
            print(f"CRAWLING: {item['rank']}")

            url = item["url"]
            driver.get(url)

            driver.implicitly_wait(5)
            time.sleep(get_rand_num())
            save_data(driver.page_source, "debug.html")

            detail = retrive_detail(driver.page_source, rank)
            item["detail"] = detail
            item_data = json.dumps(item, ensure_ascii=False, indent=4)
            save_data(item_data, f"app_{item['rank']}.json")

        driver.close()

        gen_excel()
        print("saved to excel: res.xlsx")
        gen_json()
        print("saved to json: res.json")
        print("TASK SUCCESS!")

    except Exception:
        print(format_exc())
        driver.close()


if __name__ == '__main__':
    main(BASE_URL=BASE_URL, START_INDEX=START_INDEX)
    # gen_excel()
    # gen_json()