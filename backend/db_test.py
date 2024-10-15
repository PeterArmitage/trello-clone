import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Get database connection parameters
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# Construct the connection string
conn_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

print(f"Attempting to connect with: {conn_string}")

try:
    # Attempt to establish a connection
    conn = psycopg2.connect(conn_string)
    print("Successfully connected to the database.")
    
    # Create a cursor
    cur = conn.cursor()
    
    # Execute a simple query
    cur.execute("SELECT version();")
    
    # Fetch the result
    version = cur.fetchone()
    print(f"PostgreSQL version: {version[0]}")
    
    # Close the cursor and connection
    cur.close()
    conn.close()
    print("Connection closed.")
    
except psycopg2.Error as e:
    print(f"Unable to connect to the database: {e}")

print("Test completed.")