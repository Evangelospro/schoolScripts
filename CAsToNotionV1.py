# /usr/bin/python3.9

import requests
import datetime
import math
import pyfiglet
import subprocess as s
import json
import pandas as pd
import convertapi

ascii_art = pyfiglet.figlet_format("CAs To Notion\nV 1.0")
print(ascii_art)
print(f"Current Time: {datetime.datetime.now().time()}")

# Variables:
ca_url = "https://exams.englishschool.ac.cy"
login_url = f"{ca_url}/login_check"
export_url = f"{ca_url}/student/assessments/export"
print(login_url)
creds = open("creds.json", "r").read()
creds = json.loads(creds)
password = creds["password"]
username = creds["username"]
token = creds['notion_token']
convertapi.api_secret = creds["convertapi_token"]
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
already_added_CAs = requests.post(f"{notion_api_databases}/{ca_db_id}/query", headers=headers)
already_added_CAs = already_added_CAs.json()

# Initialize


def notify(notification):
    print(f"\n{notification}")
    return s.call(['notify-send', 'ES CA Tool', notification])


def main():
    s = requests.Session()
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    s.post(login_url, data={"_username": username, "_password": password, "_remember_me": ""}, headers={"User-Agent": user_agent})
    export = s.get(export_url, headers={"User-Agent": user_agent})
    open("ca.xls", "wb").write(export.content)
    convertapi.convert('xlsx', {
    'File': 'ca.xls'
    }, from_format = 'xls').save_files('ca.xlsx')
    df = pd.read_excel("ca.xlsx")
    # for every row in the dataframe
    count = 0
    for index, row in df.iterrows():
        subject = row['Unnamed: 0']
        title = row['Common Assessment Schedule']
        week = row['Unnamed: 2']
        date = row['Unnamed: 3']
        print(type(title), title)
        if type(subject) == str and type(title) == str and type(week) == str and type(date) == str:
            count +=1
            print(f"Subject: {subject} | Title: {title} | Week: {week} | Date: {date}")
            CAs_to_post = {
                "parent": {"database_id": ca_db_id},
                "properties": {
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    },
                    "Subject": {
                        "select": {
                            "name": subject
                        }
                    },
                    "Day scheduled": {
                        "date": {
                            "start": date,
                            # "remind": "19"
                        }
                    },
                    "Week": {
                        "select": {
                                "name":  week
                            }
                    },
                }
            }
            print(CAs_to_post)
            response = requests.post(notion_api_pages, headers=headers, json=CAs_to_post)
            print(response.json())
    notification = f"Done I added succesfully {count} Common Assesments to your Notion CA page!\nSo you can be organized!!!\nNow go start studying, Common Assesments are easy but you have to study for something in your life!!!\nTime taken to run is: {datetime.datetime.now() - startTime}"
    notify(notification)

main()
