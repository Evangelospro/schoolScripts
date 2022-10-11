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
from bs4 import BeautifulSoup, SoupStrainer

ascii_art = pyfiglet.figlet_format("Weduc To Notion\nV 3.0")
print(ascii_art)
print(f"Current Time: {datetime.datetime.now().time()}")

# Variables:
creds = open("creds.json", "r").read()
creds = json.loads(creds)
Password = creds["password"]
Email = creds["email"]
token = creds['token']
startTime = datetime.datetime.now()
current_date = datetime.datetime.today()
format = "%Y,%m,%d"
homeworks = []
already_added_homework_titles = []
homework_details_images = []
external_medias = []
weduc_signin_url = "https://app.weduc.co.uk/main/index/login"
weduc_homework_url = "https://app.weduc.co.uk/homework/index/index/type/list_tasks"
notion_api_pages = "https://api.notion.com/v1/pages"
notion_api_databases = "https://api.notion.com/v1/databases"
homework_db_id = "6c06d9c868ec4d6b844da5d0b3aba7e8"
headers = {
    'Authorization': f"Bearer {token}",
    'Content-Type': 'application/json',
    'Notion-Version': '2021-08-16'
}
already_added_homeworks = requests.post(f"{notion_api_databases}/{homework_db_id}/query",
                                        headers=headers)
already_added_homeworks = already_added_homeworks.json()

# Weduc Homework Buttons
all_homework = "/html/body/div[3]/main/div/div[2]/div[2]/div/header/div[2]/div/button[1]"
todo_homework = "/html/body/div[3]/main/div/div[2]/div[2]/div/header/div[2]/div/button[2]"
overdue_homework = "/html/body/div[3]/main/div/div[2]/div[2]/div/header/div[2]/div/button[3]"
done_homework = "/html/body/div[3]/main/div/div[2]/div[2]/div/header/div[2]/div/button[4]"

def diff_dates(due_to_datetime_format, title):
    result = current_date > due_to_datetime_format
    # print(f"date_comparison {title}: {result}")
    return result


def notify(notification):
    print(f"\n{notification}")
    return s.call(['notify-send', 'Weduc To Notion V3', notification])

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        driver = await browser.new_page()
        # Sign In to Weduc
        await driver.goto(weduc_signin_url)
        startup_notification = notify("Started scraping Weduc!")
        await driver.fill('input#username',Email)
        await driver.fill('input#password',Password)
        await driver.click("input#login-button")
        time.sleep(1)
        await driver.goto(weduc_homework_url)
        for already_added_homework_title in already_added_homeworks['results']:
            try:
                already_added_homework_titles.append(
                    already_added_homework_title['properties']['Assignment']['title'][0]['text']['content'])
            except IndexError:
                continue
        #Click Todo Button
        await driver.click('//*[@id="homework-content"]/div/header/div[2]/div/button[2]')
        #Wait for the titles of the homeworks to be visible
        await driver.is_visible('div.homework-tasks')
        time.sleep(2)
        page_source = await driver.inner_html('div.homework-tasks')
        tasks_soup = BeautifulSoup(page_source, "html.parser")
        print(tasks_soup)
        all_homework_found = tasks_soup.find_all('div', class_='homework-task')
        if len(all_homework_found) == 0:
            notification = f"No Homeworks were found in Weduc maybe you should have a look at this Evangelospro!!!"
            notification = notify(notification)
            return homeworks
        for homework in all_homework_found:
            teacher = homework.find('div', class_='author-avatar').img['alt']
            print(f'//*[@id="homework-content"]/div/div/div[{all_homework_found.index(homework) + 1}]')
            await driver.click(f'//*[@id="homework-content"]/div/div/div[{all_homework_found.index(homework) + 1}]/div[2]/div[1]/div[1]/div[2]/h6', force=True)
            await driver.is_visible('div.task-title mb-4')
            time.sleep(1)
            task_page_source = await driver.inner_html('//*[@id="homework-content"]')
            task_soup = BeautifulSoup(task_page_source, "html.parser")
            try:
                homework_details_images = task_soup.find('div', class_='task-content').p.find_all('img')[0]['src']
            except (IndexError, AttributeError):
                homework_details_images = [
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/No_image_available_400_x_600.svg/400px-No_image_available_400_x_600.svg.png"]
            homework_details = re.sub("<.*?>", " ", str(task_soup.find('div', class_='task-content'))).lstrip().replace("No Media Available", "")
            title = task_soup.find('div', class_='task-title mb-4').h1.text
            if title not in already_added_homework_titles:
                homework_class = str(task_soup.find('div', class_='task-title mb-4').p.text).replace("Subject: ", "").replace(
                    "\n", "")
                submission_method = task_soup.find_all('div', class_='row')[1]
                submission_method = \
                re.sub("<.*?>", " ", str(submission_method.find_all('div', class_='col-sm-6')[0].p)).split(":")[1].lstrip()
                homework_type = task_soup.find_all('div', class_='row')[1]
                homework_type = re.sub("<.*?>", " ", str(homework_type.find_all('div', class_='col-sm-6')[1].p)).split(":")[
                    1].lstrip()
                due_to = str(task_soup.find_all('div', class_='col-sm-6')[3]).split("</strong>")[1].lstrip()[:10].split("/")
                due_to_datetime_format = datetime.datetime.strptime(due_to[2] + "," + due_to[1] + "," + due_to[0], format)
                due_to = due_to[2] + due_to[1] + due_to[0]
                if diff_dates(due_to_datetime_format, title):
                    return homeworks
                else:
                    homework_media = task_soup.find_all('tr', class_="media actions text-right")
                    if len(BeautifulSoup(str(homework_media), 'html.parser', parse_only=SoupStrainer('a'))):
                        for link in BeautifulSoup(str(homework_media), 'html.parser', parse_only=SoupStrainer('a')):
                            if link.has_attr('href'):
                                external_medias.append(link['href'])
                    else:
                        external_medias = [
                            "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/No_image_available_400_x_600.svg/400px-No_image_available_400_x_600.svg.png"]
                    homeworks.append((title, homework_details, teacher, due_to, homework_type, submission_method,
                                      homework_class, homework_details_images, external_medias))
                    print(
                        f"Homework Title: {title}, \nHomework Details: {homework_details}, \nTeacher: {teacher}, \nDue To: {due_to}, \nType: {homework_type}, \nSubmission Method: {submission_method} \nClass: {homework_class} \nHomework Details Image: {homework_details_images} \nExternal Medias: {external_medias}")
            await driver.goto(weduc_homework_url)
            #Click ToDo Button
            await driver.click('//*[@id="homework-content"]/div/header/div[2]/div/button[2]')
        print(homeworks)
        await browser.close()
        return homeworks


def weduc_to_notion(homeworks):
    if len(homeworks) == 0:
        notification = f"You are already up to date!\nTime taken to run is: {datetime.datetime.now() - startTime}"
        notification = notify(notification)
    else:
        the_homeworks_were_posted = False
        for homework in homeworks:
            homework_to_post = {
                "parent": {"database_id": homework_db_id},
                "properties": {
                    "Assignment": {
                        "title": [
                            {
                                "text": {
                                    "content": f"{homework[0]}"
                                }
                            }
                        ]
                    },
                    "Details": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"{homework[1][:1999]}"
                                }
                            }
                        ]
                    },
                    "Teacher": {
                        "select": {
                            "name": f"{homework[2]}"
                        }
                    },
                    "Due": {
                        "date": {
                            "start": f"{homework[3]}"
                        }
                    },
                    "Type": {
                        "select": {
                            "name": f"{homework[4]}"
                        }
                    },
                    "Submission Method": {
                        "select": {
                            "name": f"{homework[5]}"
                        }
                    },
                    "Class": {
                        "select": {
                            "name": f"{homework[6]}"
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
            notification = f"Done I added succesfully {len(homeworks)} homeworks to your Notion homework page!\nSo you can be organized!!!\nNow go start studying, homework won't solve itself!!!\nTime taken to run is: {datetime.datetime.now() - startTime} \n Time taken to complete: Infinity"
            notification = notify(notification)

asyncio.run(main())
weduc_to_notion(homeworks)
