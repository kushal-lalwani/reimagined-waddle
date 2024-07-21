import os
import boto3
from datetime import datetime,timezone
from psycopg2 import sql
import mimetypes
BUCKET_NAME='files-bucket-a'
REGION = 'ap-south-1'
file_folder = {
        '1':'Folder-1',
        '2':'Folder-2',
        '3':'Folder-3',
        '4':'Folder-4',
        '5':'Folder-5'
}

def upload_to_s3(bucket_name,file_path, file_id, credentials):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=credentials['access_key'],
        aws_secret_access_key=credentials['secret_access_key']
    )

    file_name = os.path.basename(file_path)
    s3_path = f"{file_folder.get(file_id)}/{file_name}"
    mime_type,_=mimetypes.guess_type(file_path)

    try:
        s3_client.upload_file(file_path, bucket_name, s3_path,ExtraArgs={'ContentType':mime_type})
    except Exception as e:
        raise RuntimeError(f"Error uploading file {file_name} to S3: {str(e)}")


def store_metadata(conn, file_path, file_id):
    cur = conn.cursor()

    try:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_extension = file_name.split('.')[-1]

        file_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{file_folder.get(file_id)}/{file_name}"
        upload_datetime = datetime.now(timezone.utc)
        print(upload_datetime)

        query = sql.SQL("""
            INSERT INTO metadata.file_metadata 
            (file_name, file_size, file_extension, folder, file_url, upload_datetime) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """)
        cur.execute(query, (file_name, file_size, file_extension, file_folder.get(file_id), file_url, upload_datetime))
        conn.commit()

        print("File metadata stored successfully")
    except Exception as e:
        print(f"Error storing file metadata: {e}")


