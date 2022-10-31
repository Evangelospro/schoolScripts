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

ascii_art = pyfiglet.figlet_format("Weduc To Notion\nV 3.0")
print(ascii_art)
print(f"Current Time: {datetime.datetime.now().time()}")

# Variables:
creds = open("creds.json", "r").read()
creds = json.loads(creds)
Password = creds["password"]
Email = creds["email"]
token = creds['notion_token']
homework_db_id = creds['notion_database_id']
startTime = datetime.datetime.now()
current_date = datetime.datetime.today()
# ISO 8601 format
format = "%Y-%m-%d"
homeworks = []
weduc_signin_url = "https://app.weduc.co.uk/main/index/login"
weduc_homework_url = "https://app.weduc.co.uk/homework/index/index/type/list_tasks"
notion_api_pages = "https://api.notion.com/v1/pages"
notion_api_databases = "https://api.notion.com/v1/databases"
headers = {
    'Authorization': f"Bearer {token}",
    'Content-Type': 'application/json',
    'Notion-Version': '2021-08-16'
}
already_added_homeworks = requests.post(f"{notion_api_databases}/{homework_db_id}/query",
                                        headers=headers)
already_added_homeworks = already_added_homeworks.json()

# Weduc Homework Buttons
all_homework = '//*[@id="homework-content"]/div/header/div[2]/div/button[1]'
todo_homework = '//*[@id="homework-content"]/div/header/div[2]/div/button[2]'
overdue_homework = '//*[@id="homework-content"]/div/header/div[2]/div/button[3]'
done_homework = '//*[@id="homework-content"]/div/header/div[2]/div/button[4]'

def cleanHTML(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def diff_dates(due, current_date):
    result = current_date > due
    return result


def notify(notification):
    print(f"\n{notification}")
    return s.call(['notify-send', 'Weduc To Notion V3', notification])

def deleteFromNotion(homework_id):
    response = requests.delete(f"{notion_api_pages}/{homework_id}",
                            headers=headers)
    print(f"Deleted {homework_id} from Notion")

def postToNotion(homeworks):
    if len(homeworks) == 0:
        notify("You are already up to date!")
    else:
        the_homeworks_were_posted = False
        for homework in homeworks:
            homework_to_post = {
                "parent": {"database_id": homework_db_id},
                "properties": {
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": homework["title"]
                                }
                            }
                        ]
                    },
                    "Details": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": homework["details"][:1999]
                                }
                            }
                        ]
                    },
                    "Teacher": {
                        "select": {
                            "name": homework['teacher']
                        }
                    },
                    "Due": {
                        "date": {
                            "start": homework["due"]
                        }
                    },
                    "Class": {
                        "select": {
                            "name": homework["class"]
                        }
                    },
                }
            }
            response = requests.post(notion_api_pages,
                                    headers=headers, json=homework_to_post)
            print(response.json())
            if response.status_code == 200:
                the_homeworks_were_posted = True
                response = response.json()
                print(f"\nNotion Response:\n{response}")
        if the_homeworks_were_posted:
            notify(f"Done I added succesfully {len(homeworks)} homeworks to your Notion homework page!\nSo you can be organized!!!\nNow go start studying, homework won't solve itself!!!")

async def login(driver):
    # Login to Weduc
    await driver.goto(weduc_signin_url)
    await driver.fill('input#username',Email)
    await driver.fill('input#password',Password)
    await driver.click("input#login-button")
    await driver.wait_for_load_state("networkidle")

async def collectHomeworks(driver):
    # Collecting Homework
    await driver.goto(weduc_homework_url)
    await driver.wait_for_load_state("networkidle")
    await driver.click(todo_homework)
    await driver.wait_for_load_state("networkidle")
    # wait until the todo button is appears
    todo_homeworks = await driver.query_selector_all("#homework-content > div > div")
    for homework in todo_homeworks:
        await driver.click(todo_homework)
        await driver.wait_for_load_state("networkidle")
        title_handler = await homework.query_selector("h6")
        title = await title_handler.inner_html()
        deadline = await homework.query_selector("div.task-date")
        deadline = await deadline.inner_html()
        deadline = deadline.split(" - ")[1]
        due, remaining = deadline.split(" ", 1)
        due = due.split("/")
        # convert date to ISO 8601 format
        due = datetime.datetime.strptime(f"{due[2]}-{due[1]}-{due[0]}", format)
        due_str = due.strftime(format)
        # check if homework is already added(check both title and details as some teachers put the same title(for god's sake please don't do that:P)) and if it is overdue or has changed due date delete it and add it again
        class_ = await homework.query_selector("span")
        class_ = await class_.inner_html()
        teacher = await homework.query_selector("div.author-avatar")
        teacher = await teacher.query_selector("img")
        teacher = await teacher.get_attribute("alt")
        # click the homework to get the details
        await title_handler.click()
        await driver.wait_for_load_state("networkidle")
        # wait unitl the content is loaded
        await driver.wait_for_selector("#homework-content > div > div > div.task-content")
        details = await driver.query_selector("#homework-content > div > div > div > div > div:nth-child(3) > div.task-info-content > div > p")
        details = await details.inner_text()
        details = cleanHTML(details)
        print(f"title: {title}, details:{details}, due: {due_str}, remaining: {remaining}, class: {class_}, teacher: {teacher}")
        for added_homework in already_added_homeworks["results"]:
            if added_homework["properties"]["Title"]["title"][0]["text"]["content"] == title and details == added_homework["properties"]["Details"]["rich_text"][0]["text"]["content"]:
                if diff_dates(due, current_date):
                    print(f"Deleting {title} it is overdue")
                    deleteFromNotion(added_homework["id"])
                if added_homework["properties"]["Due"]["date"]["start"] != due_str:
                    print(f"Deleting {title} due date has changed")
                    deleteFromNotion(added_homework["id"])
                print(f"Title: {title} is already added, it is not overdue and the due date has not changed")
                break
        else:
            print(f"Title: {title} is not added, adding it...")
            homeworks.append({
                "title": title,
                "details": details,
                "due": due_str,
                "class": class_,
                "teacher": teacher
            })
    return homeworks

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        driver = await browser.new_page()
        await login(driver)
        notify("Started scraping Weduc!")
        homeworks = await collectHomeworks(driver)
        await browser.close()
        return homeworks


asyncio.run(main())
postToNotion(homeworks)
print(f"Time taken to run is: {datetime.datetime.now() - startTime}")
