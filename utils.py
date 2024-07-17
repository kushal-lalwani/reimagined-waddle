import os
import boto3
from datetime import datetime
from postgres_config import connect_to_db
from psycopg2 import sql

BUCKET_NAME = 'files-bucket-b'
REGION = 'ap-south-1'
file_folder = {
        '1':'Folder-1',
        '2':'Folder-2',
        '3':'Folder-3',
        '4':'Folder-4',
        '5':'Folder-5'
    }
def upload_to_s3(file_path, file_id):
    s3_client = boto3.client('s3')
    file_name = os.path.basename(file_path)

    try:
        s3_client.upload_file(file_path, BUCKET_NAME, f"{file_folder.get(file_id)}/{file_name}")
    except Exception as e:
        print(e)

def store_metadata(conn, file_path, file_id):
    cur = conn.cursor()

    try:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_extension = file_name.split('.')[-1]
        folder_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{file_folder.get(file_id)}/"
        file_url = f"{folder_url}{file_name}"
        upload_datetime = datetime.now()

        query = sql.SQL("""
            INSERT INTO metadata.file_metadata 
            (file_name, file_size, file_extension, folder_url, file_url, upload_datetime) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """)
        cur.execute(query, (file_name, file_size, file_extension, folder_url, file_url, upload_datetime))
        conn.commit()

        print("File metadata stored successfully")
    except Exception as e:
        print(f"Error storing file metadata: {e}")
