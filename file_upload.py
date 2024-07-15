import os
import boto3
from postgres_config import connect_to_db

def upload_to_s3(file_path):
    s3_client = boto3.client('s3')
    file_name = os.path.basename(file_path)
    file_extension = file_name.split('.')[-1]

    try:
        s3_client.upload_file(file_path,'files-bucket-a', f"{file_extension}/{file_name}")
    except Exception as e:
        print(e)


def store_metadata(file_path):
    cur = conn.cursor()

    try:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_extension = file_name.split('.')[-1]

        query = 'INSERT INTO metadata.file_metadata (file_name, file_size, file_extension ) VALUES ( %s , %s , %s)'
        cur.execute(query, (file_name, file_size, file_extension ))
        conn.commit()
        print("File metadata stored")
    except Exception as e:
        print(e)


file_paths = [
    './Files/IMG-1.png',
    './Files/IMG-2.png',
    './Files/TEXT-1.txt',
    './Files/TEXT-2.txt',
    './Files/PDF-1.pdf'
]

conn = connect_to_db()
for file_path in file_paths:
    upload_to_s3(file_path)
    store_metadata(file_path)

conn.close()
