from flask import Flask, render_template,request, redirect, url_for, flash
from helper.db_config import init_db
from flask_migrate import Migrate
from flask import session
app = Flask(__name__)
app.config['SECRET_KEY'] = 'myveryverysecretkey'


# Initialize the database
db = init_db(app)
migrate = Migrate(app, db)


import routes

if __name__ == '__main__':
    app.run()