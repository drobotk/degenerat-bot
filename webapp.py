from flask import Flask
from threading import Thread
from os import environ

app = Flask( __name__ )

@app.route('/')
def home():
    return "cock and balls"

#def run():
app.run( host = '0.0.0.0', port = environ["PORT"] )

#t = Thread( target = run )
#t.start()