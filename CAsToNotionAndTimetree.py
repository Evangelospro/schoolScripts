#!/usr/bin/python3

import requests
import datetime
import pyfiglet
import subprocess as s
import json
import pandas as pd
import convertapi
from timetree_sdk import TimeTreeApi
from timetree_sdk.models import EventRelationshipsLabelData, EventRelationshipsAttendeesData, EventRelationshipsLabel, EventRelationshipsAttendees, EventRelationships, EventAttributes, EventData, Event

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
timetree_token = creds['timetree_token']
calendar_id = creds['timetree_calendar_id']
user_id = creds['timetree_user_id']

timetree = TimeTreeApi(timetree_token)

already_added_CAs = requests.post(f"{notion_api_databases}/{ca_db_id}/query")
already_added_CAs = already_added_CAs.json()['results']

headers = {
    'Authorization': f"Bearer {token}",
    'Content-Type': 'application/json',
    'Notion-Version': '2021-08-16'
}

def clean():
    s.call(['rm', 'ca.xlsx'])
    s.call(['rm', 'ca.xls'])

def alreadyAdded(title, date):
    for already_added_CA_title in already_added_CAs:
        alreadyAddedTitle = already_added_CA_title['properties']['Title']['title'][0]['text']['content']
        alreadyAddedId = already_added_CA_title['id']
        alreadyAddedDate = already_added_CA_title['properties']['Day scheduled']['date']['start']
        if title == alreadyAddedTitle:
            if date != alreadyAddedDate:
                return alreadyAddedId
            else:
                return "Already added"
    return "Not added"

def notify(notification):
    print(f"\n{notification}")
    return s.call(['notify-send', 'ES CA Tool', notification])

def postCATimetree(title, date):
    title = title[:50]
    my_id = timetree.get_calendar_members(calendar_id).data[0].id
    print(my_id)
    label_id = 1
    print(label_id)
    event = Event(
    data=EventData(
        attributes=EventAttributes(
            title=title,
            category='schedule',
            all_day=True,
            start_at=f'{date}T00:00:00.000Z',
            end_at=f'{date}T00:00:00.000Z',
            description='',
            location='',
            start_timezone='Asia/Nicosia',
            end_timezone='Asia/Nicosia',
        ),
        relationships=EventRelationships(
            label=EventRelationshipsLabel(
                data=EventRelationshipsLabelData(
                    id=label_id,
                    type='label'
                )
            ),
            attendees=EventRelationshipsAttendees(
                data=[EventRelationshipsAttendeesData(
                    id=my_id,
                    type='user'
                )]
                )
            )
        )
    )
    response = timetree.create_event(calendar_id, event)
    print(response)

def deleteCATimetree(id):
    timetree.delete_event(id)

def deleteCANotion(id):
    response = requests.delete(f"{notion_api_pages}/{id}", headers=headers)
    print(response.json())

def postCANotion(title, subject, week, date):
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
        if alreadyAdded(title, date) == "Already added":
            print(f"Already added {title} on {date}")
        elif "-" in alreadyAdded(title, date):
            print(f"Date changed for {title} to {date}")
            deleteCANotion(alreadyAdded(title, date))
            print(f"Subject: {subject} | Title: {title} | Week: {week} | Date: {date}")
            # postCANotion(title, subject, week, date)
            postCATimetree(title, date)
            count += 1
        elif alreadyAdded(title, date) == "Not added" and type(subject) == str and subject != "Subject" and type(title) == str and type(week) == str and type(date) == str :
            if(date == "Still pending day allocation"):
                print(f"CA {title} is still pending day allocation")
            else:
                count +=1
                print(f"Subject: {subject} | Title: {title} | Week: {week} | Date: {date}")
                # postCANotion(title, subject, week, date)
                postCATimetree(title, date)
    notification = f"Done I added succesfully {count} Common Assesments to your Notion CA page!\nSo you can be organized!!!\nNow go start studying, Common Assesments are easy but you have to study for something in your life!!!\nTime taken to run is: {datetime.datetime.now() - startTime}"
    notify(notification)
    clean()

main()
