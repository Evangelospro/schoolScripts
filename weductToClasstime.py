# /usr/bin/python3.9

import pandas as pd
from datetime import datetime
import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# app: https://gitlab.com/asdoi/TimeTable
# private static final String DB_NAME = "timetabledb";

# private static final String TIMETABLE = "timetable";
# private static final String TIMETABLE_ODD = "timetable_odd";
# private static final String WEEK_ID = "id";
# private static final String WEEK_SUBJECT = "subject";
# private static final String WEEK_FRAGMENT = "fragment";
# private static final String WEEK_TEACHER = "teacher";
# private static final String WEEK_ROOM = "room";
# private static final String WEEK_FROM_TIME = "fromtime";
# private static final String WEEK_TO_TIME = "totime";
# private static final String WEEK_COLOR = "color";

# private static final String HOMEWORKS = "homeworks";
# private static final String HOMEWORKS_ID = "id";
# private static final String HOMEWORKS_SUBJECT = "subject";
# private static final String HOMEWORKS_DESCRIPTION = "description";
# private static final String HOMEWORKS_DATE = "date";
# private static final String HOMEWORKS_COLOR = "color";

# private static final String NOTES = "notes";
# private static final String NOTES_ID = "id";
# private static final String NOTES_TITLE = "title";
# private static final String NOTES_TEXT = "text";
# private static final String NOTES_COLOR = "color";

# private static final String TEACHERS = "teachers";
# private static final String TEACHERS_ID = "id";
# private static final String TEACHERS_NAME = "name";
# private static final String TEACHERS_POST = "post";
# private static final String TEACHERS_PHONE_NUMBER = "phonenumber";
# private static final String TEACHERS_EMAIL = "email";
# private static final String TEACHERS_COLOR = "color";

# private static final String EXAMS = "exams";
# private static final String EXAMS_ID = "id";
# private static final String EXAMS_SUBJECT = "subject";
# private static final String EXAMS_TEACHER = "teacher";
# private static final String EXAMS_ROOM = "room";
# private static final String EXAMS_DATE = "date";
# private static final String EXAMS_TIME = "time";
# private static final String EXAMS_COLOR = "color";


class classTimer:
    def __init__(self) -> None:
        creds = open("creds.json", "r").read()
        creds = json.loads(creds)
        self.Password = creds["password"]
        self.Email = creds["email"]
        self.weduc_signin_url = "https://app.weduc.co.uk/main/index/login"

        self.browser = sync_playwright().start()
        self.context = self.browser.chromium.launch(headless=False)
        self.page = self.context.new_page()

        self.timetable_button = '//*[@id="user-accrodian"]/div[2]/div[1]/a'
        self.next_week_button = '//*[@id="timetable-calendar"]/div[1]/div[3]/button'
        self.prev_week_button = '//*[@id="timetable-calendar"]/div[1]/div[1]/button[1]'
        self.profile_url = "https://app.weduc.co.uk/user/profile/view"

        self.dayNames = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday"}

    def login(self) -> None:
        # Login to Weduc
        self.page.goto(self.weduc_signin_url)
        self.page.fill("input#username", self.Email)
        self.page.fill("input#password", self.Password)
        self.page.click("input#login-button")
        self.page.wait_for_load_state("networkidle")
        print("Logged in to Weduc")


    def setTimetable(self, week_name) -> pd.DataFrame:
        self.page.goto(self.profile_url)
        self.page.click(self.timetable_button)
        if week_name == "WEEK_B":
            time.sleep(1)
        else:
            self.page.click(self.timetable_button)
            self.page.click(self.prev_week_button)
        # wait for the timetable to load
        self.page.wait_for_selector("div.fc-timegrid-col-frame")
        teachers = []
        fragments = []
        rooms = []
        subjects = []
        start_times = []
        end_times = []
        colors = []
        lessons = self.page.query_selector_all("div.fc-timegrid-event-harness.fc-timegrid-event-harness-inset")
        print(f"Found {len(lessons)} lessons")
        for lesson in lessons:
            lesson.click()
            soup = BeautifulSoup(self.page.content(), "html.parser")
            popover_body_div_div = soup.find("div", {"class": "popover-body"}).find("div")
            section1, section2 = popover_body_div_div.find_all("div", {"class": "popover-item"})
            section1_spans = section1.find_all("div")[1].find_all("span")
            # time in minutes from 00:00
            fragment = self.dayNames[section1_spans[0].text.split(",")[0]]
            print(fragment)
            time_start = datetime.strptime(section1_spans[1].text, "%H:%M").time()
            time_end = datetime.strptime(section1_spans[3].text, "%H:%M").time()
            section2_spans = section2.find_all("div")[1].find_all("span")
            room = section2_spans[0].text.split("Room name: ")[1]
            if not room:
                room = "N/A"
            subject = section2_spans[2].text.split("Subject name: ")[1]
            teacher = section2_spans[3].text.split("Teacher name: ")[1]
            teachers.append(teacher)
            fragments.append(fragment)
            rooms.append(room)
            subjects.append(subject)
            start_times.append(time_start.strftime("%H:%M"))
            end_times.append(time_end.strftime("%H:%M"))
            colors.append("-12627531")
        timetable = pd.DataFrame(columns=["id", "subject", "fragment", "teacher", "room", "fromtime", "totime", "color"])
        timetable["subject"] = subjects
        timetable["fragment"] = fragments
        timetable["teacher"] = teachers
        timetable["room"] = rooms
        timetable["fromtime"] = start_times
        timetable["totime"] = end_times
        timetable["color"] = colors
        return timetable

c = classTimer()
c.login()
week_a_timetable = c.setTimetable("WEEK_A").drop_duplicates(subset=["subject", "fragment", "teacher", "room", "fromtime", "totime", "color"], keep=False)
week_b_timetable = c.setTimetable("WEEK_B").drop_duplicates(subset=["subject", "fragment", "teacher", "room", "fromtime", "totime", "color"], keep=False)
# make the id column the index and auto populate it
week_a_timetable.index = range(1, len(week_a_timetable) + 1)
week_b_timetable.index = range(1, len(week_b_timetable) + 1)
week_a_timetable["id"] = week_a_timetable.index
week_b_timetable["id"] = week_b_timetable.index

# close the browser
c.context.close()

exams = pd.DataFrame(columns=["id", "subject", "teacher", "room", "date", "time", "color"])
homeworks = pd.DataFrame(columns=["id", "subject", "description", "date", "color"])
notes = pd.DataFrame(columns=["id", "title", "text", "color"])
teachers_sheet = pd.DataFrame(columns=["id", "name", "post", "phonenumber", "email", "color"])

# do not make first column empty
with pd.ExcelWriter("results/Timetable_Backup.xlsx") as writer:
    exams.to_excel(writer, sheet_name="exams", index=False)
    homeworks.to_excel(writer, sheet_name="homeworks", index=False)
    notes.to_excel(writer, sheet_name="notes", index=False)
    teachers_sheet.to_excel(writer, sheet_name="teachers", index=False)
    week_a_timetable.to_excel(writer, sheet_name="timetable", index=False)
    week_b_timetable.to_excel(writer, sheet_name="timetable_odd", index=False)


print("Done results saved to results/Timetable_Backup.xlsx")
