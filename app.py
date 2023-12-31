from flask import Flask, render_template
from src.riot_api import setup_api_key

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route("/screen-saver", endpoint='screen-saver')
def hello_world():
    return render_template('screen-saver.html')

setup_api_key()