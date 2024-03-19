from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import openai
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import random
import math
from cachetools import TTLCache

otp_cache = TTLCache(maxsize=100, ttl=300)

app = Flask(__name__)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print(openai.api_key)
assistant_id = "asst_JP3dOs2Oij1DpUNCdDO4eaHe"
thread = None
valid_username = "User"
valid_password = "Gateway"
def send_email():

    sender = "ritik.jain@infobeans.com"
    receivers = ["deepesh.bhatia@infobeans.com"]
    app_password = "mrocgksyvdbyeidp"

    msg = MIMEMultipart()
    msg['Subject'] = "Speed Up Verification: Your OTP Shortcut Inside"
    msg['From'] = sender
    msg['To'] = ','.join(receivers)  # should be a string

    digits = "0123456789"
    OTP = ""

    for i in range(6):
        OTP += digits[math.floor(random.random()*10)]
        
    otp = OTP

    # Store OTP in the cache
    otp_cache['email_otp'] = otp

    # format body of the email (html or string)
    body_html = """
        
        <p>Please enter the OTP (One-Time Password) to verify your identity. Thank you!</p>

        <p>{}</p>
    """.format(otp)
    body_html_content = MIMEText(body_html, 'html')
    msg.attach(body_html_content)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, receivers, msg.as_string())
        server.quit()
        print("Success")

    except smtplib.SMTPException:
        print("Error: unable to send email")

# Function to verify OTP
@app.route('/api/verify', methods=['POST'])
def verify_otp():
    data = request.get_json()
    user_input = data.get('user_input')
    stored_otp = otp_cache.get('email_otp')
    if stored_otp == user_input:
        # print("OTP verified successfully!")
        return jsonify({'status': 'success', 'message': 'Login successful'})
    else:
        # print("Invalid OTP. Please try again.")
        return jsonify({'message': 'Invalid username or password'})

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').lower()
        password = data.get('password', '').lower()

        if username and password:
            if username == valid_username.lower() and password == valid_password.lower():
                send_email()
                return jsonify({'status': 'success', 'message': 'Login successful'})
            else:
                return jsonify({'message': 'Invalid username or password'})
        else:
            return jsonify({'message': 'Missing username or password'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/process_request', methods=['POST'])
def ask_question():
    try:
        global thread
        user_question = request.json.get('user_question')
        a_thread = request.json.get('thread_id')
        
        if not a_thread:
            if not thread:
                thread = client.beta.threads.create()
                print(thread.id)
                print(thread)
        else:
            if not thread:
                thread = client.beta.threads.create()
            thread.id = a_thread
            print(thread.id)
            print(thread)

        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_question
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "completed":
                break

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        latest_message = messages.data[0]
        text = latest_message.content[0].text.value
        text = text.replace('\n', ' ')
        result = re.sub(r'\【.*?\】', '', text)

        return jsonify({'response': result, 'thread_id': thread.id})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
