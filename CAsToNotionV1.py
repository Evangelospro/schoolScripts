# /usr/bin/python3.9

import asyncio
import re
import datetime
import pyfiglet
import subprocess as s
from playwright.async_api import async_playwright
import json
import requests
import time
import pandas as pd

ascii_art = pyfiglet.figlet_format("CAs To Notion\nV 1.0")
print(ascii_art)
print(f"Current Time: {datetime.datetime.now().time()}")

# Variables:
ca_website = "https://ca.englishschool.ac.cy"
Common_Assesment_URL = "https://ca.englishschool.ac.cy/student/assessments"
creds = open("/home/evangelospro/.local/bin/CAsToNotion/creds.json", "r").read()
creds = json.loads(creds)
password = creds["password"]
username = creds["username"]
token = creds['token']
already_added_CAs_titles = []
startTime = datetime.datetime.now()
notion_api_pages = "https://api.notion.com/v1/pages"
notion_api_databases = "https://api.notion.com/v1/databases"
ca_db_id = "be3ffad9fb4247eb8f0f5704c8b7835a"
headers = {
    'Authorization': f"Bearer {token}",
    'Content-Type': 'application/json',
    'Notion-Version': '2021-08-16'
}
already_added_CAs = requests.post(f"{notion_api_databases}/{ca_db_id}/query",
                                  headers=headers)
already_added_CAs = already_added_CAs.json()
login_button = "/html/body/div[2]/section/div[2]/div/div/form/div[5]/button"

# Initialize


def notify(notification):
    print(f"\n{notification}")
    return s.call(['notify-send', 'ES CA Tool', notification])


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        driver = await browser.new_page()
        await driver.goto(ca_website)
        startup_notification = notify("Started scraping ES CA Tool!")
        await driver.fill("input#username", username)
        await driver.fill("input#password", password)
        await driver.click('//*[@id="loginForm"]/div[5]/button')
        await driver.goto(Common_Assesment_URL)
        page_source = await driver.inner_html('div.col-sm-12')
        await browser.close()
    # page_source = driver.page_source
    df_list = pd.read_html(page_source)
    df = df_list[0]
    # df = df.iloc[:, :-1]
    for already_added_CA_title in already_added_CAs['results']:
        already_added_CAs_titles.append(
            already_added_CA_title['properties']['Title']['title'][0]['text']['content'])
    for ca in df["Subject"].index:
        if df["Title"][ca] not in already_added_CAs_titles and df["Day scheduled"][
            ca] != "Still pending day allocation":
            day_scheduled_formated = df["Day scheduled"][ca].split("-")
            day_scheduled_formated = day_scheduled_formated[2] + "-" + day_scheduled_formated[1] + "-" + \
                                     day_scheduled_formated[0]
            CAs_to_post = {
                "parent": {"database_id": ca_db_id},
                "properties": {
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": df["Title"][ca]
                                }
                            }
                        ]
                    },
                    "Subject": {
                        "select": {
                            "name": df["Subject"][ca]
                        }
                    },
                    "Day scheduled": {
                        "date": {
                            "start": day_scheduled_formated,
                            # "remind": "19"
                        }
                    },
                    "Week": {
                        "select": {
                                "name":  df["Week"][ca]
                            }
                    },
                }
            }
            print(CAs_to_post)
            response = requests.post(notion_api_pages, headers=headers, json=CAs_to_post)
            print(response.json())
    notification = f"Done I added succesfully {len(list(df))} Common Assesments to your Notion CA page!\nSo you can be organized!!!\nNow go start studying, Common Assesments are easy but you have to study for something in your life!!!\nTime taken to run is: {datetime.datetime.now() - startTime}"
    notification = notify(notification)

asyncio.run(main())
