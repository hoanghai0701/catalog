from flask import Flask

app = Flask(__name__)
app.secret_key = 'very_secret_key'
app.debug = True

from handlers import *
