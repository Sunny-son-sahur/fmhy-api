import threading
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "FMHY Bot is running!"

@app.route('/health')
def health():
    return {"status": "ok"}

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
