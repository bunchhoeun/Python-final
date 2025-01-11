import mysql.connector
from flask_sqlalchemy import SQLAlchemy

def init_db(app):
    # Database configuration
    db_name = 'PyFinal'
    db_user = 'root'
    db_password = ''  # Replace with your MySQL password if applicable
    db_host = 'localhost'

    # Create the database if it doesn't exist
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password
    )
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    connection.close()

    # Configure SQLAlchemy to use the newly created database
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db = SQLAlchemy(app)
    return db
