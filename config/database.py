import mysql.connector

from mysql.connector import Error
import os

from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),         
            password=os.getenv('DB_PASS')
        )
        return connection
    except Error as e:
        print("Error connection to db: {e}")
        return None
