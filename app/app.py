from flask import Flask

app = Flask(__name__)
app.secret_key = 'very_secret_key'
app.config['JWT_EXP'] = 3600
app.config['JWT_SCHEME'] = 'Bearer'
app.debug = True
