import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables (ensure .env is in the same directory or a parent directory)
load_dotenv()

def send_test_email():
    """Sends a test email using Gmail."""

    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    # print(gmail_user)
    # print(gmail_app_password)

    if not gmail_user or not gmail_app_password:
        print("Error: Gmail credentials not found in environment variables.")
        return

    recipient = "raoulbia.ai@gmail.com"  # Replace with a test recipient email address
    subject = "Test Email from Script"
    body = "This is a test email sent from a Python script."

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_app_password)
        text = msg.as_string()
        server.sendmail(gmail_user, recipient, text)
        server.quit()
        print(f"Email sent to {recipient}.")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()  # Print detailed traceback for debugging


if __name__ == "__main__":
    send_test_email()