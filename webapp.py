from flask import Flask
from os import environ

app = Flask( __name__ )

@app.route('/')
def home():
    return "cock and balls"

app.run( host = '0.0.0.0', port = environ["PORT"] )
