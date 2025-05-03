import smtplib
from email.mime.text import MIMEText

EMAIL_ADDRESS = "dericvictor2@gmail.com"           # your Gmail
EMAIL_PASSWORD = "ktphrdunbhbbeehp"             # paste app password with no spaces
TO_EMAIL = "discodrv@gmail.com"          # can be same or different

msg = MIMEText("✅ Test successful! Your app password works.")
msg["Subject"] = "Test Email"
msg["From"] = EMAIL_ADDRESS
msg["To"] = TO_EMAIL

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
    print("✅ Email sent successfully!")
except smtplib.SMTPAuthenticationError as e:
    print("❌ Authentication failed:", e)
