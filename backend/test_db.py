import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

print(f"Attempting to connect with URL: {SQLALCHEMY_DATABASE_URL}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

try:
    connection = engine.connect()
    print("Successfully connected to the database!")
    connection.close()
except Exception as e:
    print(f"An error occurred: {e}")