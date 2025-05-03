# ---------------------- FILE: daily_scheduler.py ----------------------
# This script runs in the background to email your summary every day at 11 PM

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Import functions from app.py
from step6_mail import load_nutrition_data, find_closest_food, get_nutrients, generate_summary_from_totals, nutrients

EMAIL_ADDRESS = "dericvictor2@gmail.com"           # your Gmail
EMAIL_PASSWORD = "ktphrdunbhbbeehp"             # paste app password with no spaces
TO_EMAIL = "discodrv@gmail.com"          # can be same or different
LOG_FILE = "daily_meal_logs.csv"

# --------- Email Sending Function --------- #
def send_email(subject, body, to):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# --------- Generate Daily Summary Function --------- #
def get_today_summary():
    if not os.path.exists(LOG_FILE):
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    df = pd.read_csv(LOG_FILE)
    df = df[df["Timestamp"].str.contains(today)]

    if df.empty:
        return None

    nutrition_df = load_nutrition_data()
    total = pd.DataFrame(columns=["Nutrient", "Total Intake"])
    total_values = [0.0] * len(nutrients)

    for entry in df["Entry"]:
        for d in entry.lower().split(" and "):
            matched = find_closest_food(d.strip())
            vals = get_nutrients(matched)
            total_values = [x + y for x, y in zip(total_values, vals)]

    result = pd.DataFrame({
        "Nutrient": [n.replace("_", " ").title() for n in nutrients],
        "Total Intake": [round(v, 2) for v in total_values]
    })

    return result

# --------- Scheduled Job Function --------- #
def job():
    summary_df = get_today_summary()
    if summary_df is not None:
        html_summary = generate_summary_from_totals(summary_df).replace("\n", "<br>")
        send_email("\U0001F4DD Your Daily Nutrition Summary", html_summary, TO_EMAIL)
        print(f"✔️ Summary sent at {datetime.now()}")
    else:
        print(f"ℹ️ No meals logged today. Skipping email at {datetime.now()}.")

# --------- Start Scheduler --------- #
scheduler = BlockingScheduler()
scheduler.add_job(job, 'cron', hour=21, minute=00)

if __name__ == "__main__":
    print("📅 Scheduler started. Waiting to send summary every night at 9:00 PM...")
    scheduler.start()
