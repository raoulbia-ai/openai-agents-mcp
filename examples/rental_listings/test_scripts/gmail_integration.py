"""For GMAIL_APP_PASSWORD, you'll need to enable 2-Step Verification in your Google Account settings 
and then generate an app password.  See https://support.google.com/accounts/answer/185833?hl=en for instructions."""

# Placeholder for gmail integration with rental listings agent.
# This is a starting point and will be expanded later.

from agents.run_context import RunContextWrapper
from agents import Agent, function_tool
from openai import OpenAI
import imaplib
from email.parser import BytesParser
from email.policy import default

# Load environment variables
import os
from dotenv import load_dotenv
load_dotenv()

openai_api_key = os.environ.get("OPENAI_API_KEY")
gmail_user = os.environ.get("GMAIL_USER")
gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

@function_tool
def check_emails(wrapper: RunContextWrapper[None]) -> str:
    """Check emails in the inbox and return a summary, focusing on rental-related inquiries.

    Returns:
        str: A summary of relevant emails, or an error message if something goes wrong.
    """
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(gmail_user, gmail_app_password)
        mail.select('inbox')

        # Search for emails with specific keywords in subject or body
        status, data = mail.search(None, '(OR (SUBJECT "Rental Application") (SUBJECT "Inquiry") (BODY "looking for a rental"))')
        if status != 'OK':
            return "Error: Could not retrieve emails from the inbox."

        email_ids = data[0].split()
        num_emails = len(email_ids)
        summaries = []

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                summaries.append(f"Error fetching email {email_id.decode()}")
                continue

            msg = BytesParser(policy=default).parsebytes(msg_data[0][1])
            subject = msg.get("Subject", "[No Subject]")
            sender = msg.get("From", "[No Sender]")
            # Get a plain text version of the body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                        break
            else:
                if msg.get_content_type() == "text/plain":
                    body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='ignore')

            body_snippet = body.strip()[:100] + ("..." if len(body.strip()) > 100 else "")
            summaries.append(f"From: {sender}, Subject: {subject}, Snippet: {body_snippet}")

        return "\n".join(summaries) if summaries else "No relevant emails found."


    except imaplib.IMAP4.error as e:
        return f"IMAP Error: {str(e)}"
    except TimeoutError as e:
        return f"Connection Timeout Error: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# Create the Gmail integration agent
gmail_integration_agent = Agent(
    name="Gmail Integration Agent",
    instructions="You are an agent that interacts with Gmail for rental listings.",
    tools=[check_emails]
)