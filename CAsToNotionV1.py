#!/usr/bin/python3

import requests
import datetime
import pyfiglet
import subprocess as s
import json
import pandas as pd
import convertapi

startTime = datetime.datetime.now()

ascii_art = pyfiglet.figlet_format("CAs To Notion\nV 1.0")
print(ascii_art)
print(f"Current Time: {startTime.time()}")

# Variables:
ca_url = "https://exams.englishschool.ac.cy"
login_url = f"{ca_url}/login_check"
export_url = f"{ca_url}/student/assessments/export"
notion_api_pages = "https://api.notion.com/v1/pages"
notion_api_databases = "https://api.notion.com/v1/databases"

creds = open("creds.json", "r").read()
creds = json.loads(creds)
password = creds["password"]
username = creds["username"]
token = creds['notion_token']
convertapi.api_secret = creds["convertapi_token"]
ca_db_id = creds['ca_db_id']

headers = {
    'Authorization': f"Bearer {token}",
    'Content-Type': 'application/json',
    'Notion-Version': '2021-08-16'
}

def alreadyAdded(title, date):
    already_added_CAs = requests.post(f"{notion_api_databases}/{ca_db_id}/query", headers=headers)
    already_added_CAs = already_added_CAs.json()['results']
    for already_added_CA_title in already_added_CAs:
        alreadyAddedTitle = already_added_CA_title['properties']['Title']['title'][0]['text']['content']

        alreadyAddedDate = already_added_CA_title['properties']['Day scheduled']['date']['start']
        if title == alreadyAddedTitle and date == alreadyAddedDate:
            return True
    return False

def notify(notification):
    print(f"\n{notification}")
    return s.call(['notify-send', 'ES CA Tool', notification])


def postCA(title, subject, week, date):
    data = {
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
    response = requests.post(notion_api_pages, headers=headers, json=data)
    print(response.json())

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
        if alreadyAdded(title, date):
            print(f"Already added {title} on {date}")
        elif type(subject) == str and subject != "Subject" and type(title) == str and type(week) == str and type(date) == str :
            if(date == "Still pending day allocation"):
                print(f"CA {title} is still pending day allocation")
            else:
                count +=1
                print(f"Subject: {subject} | Title: {title} | Week: {week} | Date: {date}")
                postCA(title, subject, week, date)
    notification = f"Done I added succesfully {count} Common Assesments to your Notion CA page!\nSo you can be organized!!!\nNow go start studying, Common Assesments are easy but you have to study for something in your life!!!\nTime taken to run is: {datetime.datetime.now() - startTime}"
    notify(notification)

main()
