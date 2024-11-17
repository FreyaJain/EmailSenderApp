**Email Automation Tool**

Overview
The Email Automation Tool is a powerful and user-friendly application designed to simplify email communication and scheduling. With features like personalized email generation, Google Sheets integration, CSV uploads, and real-time analytics, this tool is perfect for businesses and individuals looking to streamline their email outreach efforts.

**Features**

**1. Compose Emails**
Manual Email Composition:
Upload data from a CSV file or a Google Sheet.
Automatically detect placeholders based on the column names (e.g., {{ Name }}, {{ Company }}).
Send personalized emails to multiple recipients by replacing placeholders with actual data.

Generate Emails Using AI:
Leverage OpenAI’s GPT-3.5/4 models to generate professional and personalized emails dynamically.
Automatically populate email content using placeholders derived from your dataset.

2. **Email Scheduling**
Schedule emails to be sent at a specific date and time.
Control the sending rate to avoid email provider limitations.
Automatically update the email status (Sent, Pending, Failed).

3. **Google Sheets Integration and Personalization**
Fetch data directly from Google Sheets using its Sheet ID and range.
Ensure real-time data updates for accurate email personalization.

4. **Analytics Dashboard**
Overview Tab: Monitor key metrics like the number of sent, pending, and failed emails.
Trends Tab: Visualize trends in email statuses over time using Plotly charts.

5. **Customizable UI**
Custom CSS for a sleek and professional interface.
Sidebar navigation for seamless interaction with different functionalities.


**How to Use**
Step 1: Installation
Clone the repository and install the required Python packages:
git clone <repository-url>
cd email-automation-tool
pip install -r requirements.txt

Step 2: Set Up Google API
Enable Google Sheets and Gmail APIs in your Google Cloud Console.
Download the credentials.json file and place it in the project directory.

Step 3: Run the App
Run the application using Streamlit:
streamlit run app.py

**File Structure**

email-automation-tool/
├── app.py                # Main application script <br>
├── database.py           # Database helper functions <br>
├── requirements.txt      # Python dependencies <br>
├── token.json            # OAuth token file (generated after authentication) <br>
├── credentials.json      # Google API credentials <br>
├── README.md             # Project documentation <br>
├── emails.db             # SQLite database for email scheduling <br>

**Dependencies/Python Libraries**:
os
pandas
streamlit
google-auth
google-auth-oauthlib
google-api-python-client
email.mime.text import MIMEText
email.mime.multipart import MIMEMultipart
sqlite3
openai
plotly
datetime
threading
