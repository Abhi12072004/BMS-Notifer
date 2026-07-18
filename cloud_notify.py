# BookMyShow Ticket-Release Notifier - Cloud (GitHub Actions) version
# Runs ONCE per invocation. Checks the date-specific BMS page for Palazzo
# showtimes, and if found, sends an urgent push via ntfy.sh.
 
import os
import re
import time
 
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
 
MOVIE_URL_BASE = "https://in.bookmyshow.com/movies/chennai/the-odyssey/buytickets/ET00480917"
TARGET_DATE = os.environ.get("TARGET_DATE", "20260722")
CHECK_URL = f"{MOVIE_URL_BASE}/{TARGET_DATE}"
 
CINEMA_KEYWORD = "Palazzo"
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "abhijeeth-bms-odyssey-9247")
 
TIME_PATTERN = re.compile(r"\b\d{1,2}:\d{2}\s?(AM|PM|am|pm)\b")
NOT_OPEN_PHRASES = ["not available", "not yet open", "coming soon", "no shows"]
 
 
def build_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)
 
 
def check_page(driver):
    driver.get(CHECK_URL)
    time.sleep(5)
    text = driver.find_element("tag name", "body").text
    print(f"PAGE LENGTH: {len(text)} | FIRST 300 CHARS: {text[:300]}")
    if CINEMA_KEYWORD.lower() not in text.lower():
        return False
 
    idx = text.lower().find(CINEMA_KEYWORD.lower())
    window = text[idx: idx + 600]
 
    if any(p in window.lower() for p in NOT_OPEN_PHRASES):
        return False
 
    return bool(TIME_PATTERN.search(window))
 
 
def send_ntfy(title, message):
    resp = requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "urgent",
            "Tags": "rotating_light",
            "Click": CHECK_URL,
        },
        timeout=15,
    )
    print(f"ntfy status: {resp.status_code}")
 
 
def main():
    print(f"Checking: {CHECK_URL}")
    driver = build_driver()
    try:
        found = check_page(driver)
    finally:
        driver.quit()
 
    if found:
        print(f"FOUND - Palazzo showtimes are live for {TARGET_DATE}. Sending push.")
        send_ntfy(
            "BookMyShow - Booking Open!",
            f"Palazzo IMAX showtimes are live for {TARGET_DATE}. Tap to book.",
        )
    else:
        print("Not open yet.")
 
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"found={'true' if found else 'false'}\n")
 
 
if __name__ == "__main__":
    main()
