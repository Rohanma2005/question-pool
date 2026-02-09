from app import create_app
from app.extensions import db
from app import models
from flask import Flask
from flask_cors import CORS

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
