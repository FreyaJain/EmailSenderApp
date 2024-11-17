import pandas as pd
import streamlit as st
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sqlite3

from api_integration import get_gmail_service

def initialize_database():
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled',
            scheduled_time TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Save email details to the database
def save_email_to_database(recipient_email, subject, body, scheduled_time):
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO emails (recipient_email, subject, body, scheduled_time)
        VALUES (?, ?, ?, ?)
    """, (recipient_email, subject, body, scheduled_time))
    conn.commit()
    conn.close()

# Retrieve unsent emails from the database
def get_unsent_emails():
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM emails
        WHERE status = 'scheduled' AND scheduled_time <= ?
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    emails = cursor.fetchall()
    conn.close()
    return emails

# Update email status in the database
def update_email_status(email_id, status):
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE emails
        SET status = ?
        WHERE id = ?
    """, (status, email_id))
    conn.commit()
    conn.close()
    
#send email
def send_email(to_email, subject, body):
    service = get_gmail_service()
    if service:
        message = MIMEMultipart()
        message["to"] = to_email  # Ensure the recipient email is correctly set
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))
        raw_message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
        try:
            service.users().messages().send(userId="me", body=raw_message).execute()
            st.success(f"Email sent to {to_email}")
        except HttpError as error:
            st.error(f"An error occurred while sending email: {error}")
 
#replace placeholders
def replace_placeholders(template, row):
    for col, value in row.items():
        if pd.notna(value):  # Only replace if the value is not NaN
            template = template.replace(f"{{{{ {col} }}}}", str(value))
    return template

# Schedule emails with database integration
def schedule_emails_with_db(data, subject, email_template, scheduled_time):
    try:
        for _, row in data.iterrows():
            recipient_email = row.get("Recipient Email")
            personalized_body = replace_placeholders(email_template, row)
            save_email_to_database(recipient_email, subject, personalized_body, scheduled_time)
        st.success("Emails scheduled successfully!")
    except Exception as e:
        st.error(f"An error occurred while scheduling emails: {e}")

# Initialize database
initialize_database()


