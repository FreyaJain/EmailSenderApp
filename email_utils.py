import os
import openai
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Function to generate email using LLM
def generate_email_with_llm(prompt, row):
    for placeholder, value in row.items():
        prompt = prompt.replace(f"{{{{ {placeholder} }}}}", str(value))
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=300
        )
        return response.choices[0].text.strip()
    except Exception as e:
        st.error(f"An error occurred while generating email: {e}")
        return None
    
