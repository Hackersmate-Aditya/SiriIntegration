from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
import re

app = Flask(__name__)

load_dotenv()

# Dummy user credentials (replace these with your actual authentication logic)
valid_username = "User"
valid_password = "Gateway"


openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print(openai.api_key)
assistant_id = "asst_JP3dOs2Oij1DpUNCdDO4eaHe"
thread = None

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        # username = data.get('username')
        # password = data.get('password')
        username = data.get('username', '').lower()
        password = data.get('password', '').lower()

        if username and password:
            if username == valid_username.lower() and password == valid_password.lower():
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
        username = request.json.get('username')
        password = request.json.get('password')
        user_question = request.json.get('user_question')
        a_thread = request.json.get('thread_id')

        # Check the validity of the username and password
        # if username != valid_username or password != valid_password:
        #     return jsonify({'status': 'error', 'message': 'Invalid username or password'})

        # Rest of your code for processing the user's question
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
