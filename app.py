from flask import Flask, request
import os
import sys
import json

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!!!', 200

if __name__ == '__main__':
    app.run(debug=True)
