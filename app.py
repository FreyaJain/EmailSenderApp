import os
import pandas as pd
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import openai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import plotly.express as px
import time
import threading

from database import replace_placeholders, send_email, schedule_emails_with_db, get_unsent_emails, update_email_status

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://mail.google.com/"]

# Function to get Google Sheet data
def get_google_sheet_data(sheet_id, sheet_range):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    try:
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=sheet_id, range=sheet_range).execute()
        values = result.get("values", [])
        if not values:
            st.warning("No data found in the Google Sheet.")
            return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])  # Assuming first row as headers
    except HttpError as err:
        st.error(f"An error occurred: {err}")
        return pd.DataFrame()

# Add custom CSS
st.markdown("""
    <style>
    body {
        font-family: Arial, sans-serif;
    }
    .main-heading {
        font-size: 32px; 
        font-weight: bold; 
        text-align: left; 
        color: #333;
    }
    .sub-heading {
        font-size: 24px; 
        font-weight: bold; 
        margin-bottom: 10px; 
        color: #555;
    }
    .sidebar {
        background-color: #f7f7f7;
        padding: 15px;
    }
    .analytics-card {
        background-color: #f9f9f9; 
        border-radius: 10px; 
        padding: 15px; 
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Main Heading
st.markdown("<h1 class='main-heading'>Email Automation Tool</h1>", unsafe_allow_html=True)

# Compose Email Section
st.markdown("<h2 class='sub-heading'>Compose Email</h2>", unsafe_allow_html=True)

# Input Fields for Subject and Email Body
subject = st.text_input("Subject", placeholder="Enter email subject")
email_template = st.text_area("Body", placeholder="Enter email body with placeholders like {{ Name }}, {{ Company }}")

# Sidebar Mode Selection
mode = st.sidebar.radio("Choose Mode", ["Manual", "Generate Email"], key="email_mode")

# Manual Mode
if mode == "Manual":
    data_source = st.sidebar.selectbox("Upload Data", ["Upload CSV", "Google Sheet"], key="data_source")
    if data_source == "Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv", key="csv_manual")
        if uploaded_file is not None:
            data = pd.read_csv(uploaded_file)
            st.write("Data from CSV:")
            st.dataframe(data)

            # Automatically detect placeholders based on column names
            placeholders = [f"{{{{ {col} }}}}" for col in data.columns]
            st.info(f"Detected placeholders: {', '.join(placeholders)}")
            
            # Replace placeholders and send emails
            if st.button("Send Emails"):
                for index, row in data.iterrows():
                    personalized_body = replace_placeholders(email_template, row)
                    recipient_email = row.get("Recipient Email")
                    if recipient_email:
                        try:
                            send_email(recipient_email, subject, personalized_body)
                            st.success(f"Email sent to {recipient_email}")
                        except Exception as e:
                            st.error(f"An error occurred: {e}")
                    else:
                        st.warning(f"Missing recipient email for row {index}. Skipping.")

    elif data_source == "Google Sheet":
        sheet_id = st.sidebar.text_input("Enter Google Sheet ID", key="sheet_id_manual")
        sheet_range = st.sidebar.text_input("Enter Range (e.g., Sheet1!A1:D10)", key="sheet_range_manual")
        if st.sidebar.button("Fetch Google Sheet Data", key="fetch_google_sheet_manual"):
            data = get_google_sheet_data(sheet_id, sheet_range)
            st.write("Data from Google Sheet:")
            st.dataframe(data)

            placeholders = [f"{{{{ {col} }}}}" for col in data.columns]
            st.info(f"Detected placeholders: {', '.join(placeholders)}")

            if st.button("Send Emails"):
                for index, row in data.iterrows():
                    personalized_body = replace_placeholders(email_template, row)
                    recipient_email = row.get("Recipient Email")
                    if recipient_email:
                        try:
                            send_email(recipient_email, subject, personalized_body)
                            st.success(f"Email sent to {recipient_email}")
                        except Exception as e:
                            st.error(f"An error occurred: {e}")
                    else:
                        st.warning(f"Missing recipient email for row {index}. Skipping.")

# Generate Email Mode
elif mode == "Generate Email":
    # Generate Email Mode: Create emails using an LLM
    st.header("Generate Emails Using LLM")

    # Load data
    data_source = st.sidebar.selectbox("Choose Data Source", ["Upload CSV", "Google Sheet"], key="data_source_generate")
    
    if data_source == "Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv", key="csv_generate")
        if uploaded_file:
            data = pd.read_csv(uploaded_file)
            st.write("Data from CSV:")
            st.dataframe(data)

    elif data_source == "Google Sheet":
        sheet_id = st.sidebar.text_input("Enter Google Sheet ID", key="sheet_id_generate")
        sheet_range = st.sidebar.text_input("Enter Range (e.g., Sheet1!A1:D10)", key="sheet_range_generate")
        if st.sidebar.button("Fetch Google Sheet Data", key="fetch_google_sheet_generate"):
            data = get_google_sheet_data(sheet_id, sheet_range)  # Function for Google Sheets data retrieval
            st.write("Data from Google Sheet:")
            st.dataframe(data)

    # Automatically extract placeholders from column names
    placeholders = []
    if not data.empty:
        placeholders = [f"{{{{ {col} }}}}" for col in data.columns]
        st.info(f"Detected placeholders: {', '.join(placeholders)}")

    # Generate email prompt dynamically
    try:
     if placeholders:
        prompt = f"""
        Write a professional email offering a special promotion to {placeholders[0]}. The email should be personalized 
        with their name, product details, and any relevant information from the list. 
        Include a call-to-action and be professional, yet friendly.
        """
     else:
        prompt = "Type your prompt here..."  # Default prompt if no placeholders detected

    # Show the prompt for preview
     st.text_area("Generated Prompt Example", value=prompt, height=200)

    # Generate Emails
     if not data.empty and st.button("Generate Emails"):
        for _, row in data.iterrows():
            # Automatically replace placeholders in the prompt
            personalized_prompt = replace_placeholders(prompt, row)

            try:
                # Use OpenAI's new API method for generating email content (using the 'completions.create()' method in version 1.0.0)
                response = openai.completions.create(
                    model="gpt-3.5-turbo",  # You can also use "gpt-4"
                    prompt=personalized_prompt,
                    max_tokens=500,  # Adjust token limit as needed
                    temperature=0.7
                )
                email_content = response['choices'][0]['text'].strip()

                # Display the generated email for the current row
                st.success(f"Generated Email for {row.get('Name', 'Recipient')}:\n{email_content}")

            except Exception as e:
                st.error(f"An error occurred while generating email: {e}")
    except:
        st.write("API token expired")  
  
#Email Scheduler   
st.markdown("<h2 class='sub-heading'>Schedule Email</h2>", unsafe_allow_html=True)
scheduled_time = st.text_input("Schedule Time", placeholder="YYYY-MM-DD HH:MM")
send_rate = st.slider("Send Rate (emails/hour)", min_value=1, max_value=100, value=10)
if st.button("Schedule Emails"):
    if not subject or not email_template:
        st.error("Please provide a subject and email body.")
    elif not uploaded_file and data_source == "Upload CSV":
        st.error("Please upload a CSV file.")
    elif data_source == "Google Sheet" and (not sheet_id or not sheet_range):
        st.error("Please provide Google Sheet ID and Range.")
    else:
        st.success("Emails scheduled successfully!")


# Section 3: Analytics Dashboard
st.sidebar.markdown("<h2>Analytics Dashboard</h2>", unsafe_allow_html=True)
analytics_tab = st.sidebar.radio("Choose View", ["Overview", "Trends"], key="analytics_view")

def fetch_analytics():
    conn = sqlite3.connect("emails.db")
    query = """
    SELECT 
        COUNT(CASE WHEN status = 'sent' THEN 1 END) AS total_sent,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) AS total_pending,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) AS total_failed
    FROM emails
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def fetch_status_trend():
    conn = sqlite3.connect("emails.db")
    query = """
    SELECT status, COUNT(*) as count, DATE(scheduled_time) as date
    FROM emails
    GROUP BY DATE(scheduled_time), status
    ORDER BY DATE(scheduled_time)
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

if analytics_tab == "Overview":
    st.markdown("<div class='analytics-card'><h3>Overview</h3>", unsafe_allow_html=True)
    analytics_data = fetch_analytics()
    if not analytics_data.empty:
        sent = analytics_data['total_sent'].iloc[0]
        pending = analytics_data['total_pending'].iloc[0]
        failed = analytics_data['total_failed'].iloc[0]
        st.metric("Emails Sent", sent)
        st.metric("Emails Pending", pending)
        st.metric("Emails Failed", failed)
    else:
        st.warning("No data available.")

elif analytics_tab == "Trends":
    st.markdown("<div class='analytics-card'><h2>Email Trends</h2>", unsafe_allow_html=True)
    trend_data = fetch_status_trend()
    if not trend_data.empty:
        fig = px.line(trend_data, x="date", y="count", color="status", title="Email Status Trends Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No trend data available.")

# Final background thread for sending emails
def run_email_scheduler():
    while True:
        unsent_emails = get_unsent_emails()
        for email in unsent_emails:
            email_id, recipient_email, subject, body, status, scheduled_time = email
            try:
                send_email(recipient_email, subject, body)
                update_email_status(email_id, "sent")
                time.sleep(3600 / send_rate)
            except Exception as e:
                update_email_status(email_id, "failed")
                st.error(f"Error: {e}")
        time.sleep(10)

threading.Thread(target=run_email_scheduler, daemon=True).start()
