from flask import Flask
from flask_mongoengine import MongoEngine, MongoEngineSessionInterface
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = MongoEngine(app)
app.session_interface = MongoEngineSessionInterface(db)

from .routes import *

