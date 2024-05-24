import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',  # Replace with your MySQL host, usually 'localhost' or '127.0.0.1'
        user='root',  # Replace with your MySQL username
        database='virtual_classroom'  # The name of your database
    )
    return connection
