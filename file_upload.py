import os
import boto3
from flask import Flask, request, jsonify , session
from utils import upload_to_s3,store_metadata
from postgres_config import connect_to_db
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

app = Flask(__name__)

UPLOAD_FOLDER = 'Uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.secret_key = 'SECRET'

@app.route('/login', methods=['POST'])
def login():
    access_key = request.form['access_key']
    secret_key = request.form['secret_access_key']
    session['credentials'] = {
        'access_key': access_key,
        'secret_access_key': secret_key
    }
    try:

        sts_client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        sts_response = sts_client.get_caller_identity()
        return jsonify({
            'message': 'Login successful!',
            'user_arn': sts_response['Arn'],
            'user_id': sts_response['UserId']
        }), 200

    except (NoCredentialsError, PartialCredentialsError, ClientError) as e:
        return jsonify({'message': f'Invalid credentials: {str(e)}'}), 401

@app.route('/list-buckets', methods=['GET'])
def list_buckets():
    if 'credentials' not in session:
        return jsonify({"error": "AWS credentials are required. Please log in first."}), 401

    credentials = session['credentials']

    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=credentials['access_key'],
            aws_secret_access_key=credentials['secret_access_key']
        )

        response = s3_client.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return jsonify({'buckets': buckets}), 200

    except Exception as e:
        return jsonify({'message': f'Error listing buckets: {str(e)}'}), 500

@app.post('/upload')
def uploadFiles():
    files = request.files.getlist('files')
    ids = request.form.getlist('ids')
    bucket_name = request.form['bucket_name']
    credentials = session['credentials']
    if 'credentials' not in session:
        return jsonify({"error": "AWS credentials are required. Please log in first."}), 401

    uploaded_files = []

    if len(files) != len(ids):
        return jsonify({"error": "Number of files and IDs must match"}), 400

    conn = connect_to_db()

    for file, file_id in zip(files, ids):
        if file.filename == '':
            continue
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        upload_to_s3(bucket_name,file_path, file_id,credentials)
        store_metadata(conn, file_path,file_id)
        uploaded_files.append({"id": file_id, "filename": file.filename})

        os.remove(file_path)

    conn.close()
    return jsonify({"message": "Files uploaded successfully", "files": uploaded_files})

@app.route('/list-objects', methods=['POST'])
def list_objects():
    credentials = session['credentials']
    if 'credentials' not in session:
        return jsonify({"error": "AWS credentials are required. Please log in first."}), 401

    data = request.json
    bucket_name = data.get('bucket_name')
    folder = data.get('folder', '')
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=credentials['access_key'],
            aws_secret_access_key=credentials['secret_access_key']
        )

        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=folder,
            Delimiter='/'
        )
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-presigned-url', methods=['POST'])
def generate_presigned_url():
    credentials = session['credentials']
    if 'credentials' not in session:
        return jsonify({"error": "AWS credentials are required. Please log in first."}), 401

    data = request.json
    bucket_name = data.get('bucket_name')
    object_key = data.get('object_key')

    if not bucket_name or not object_key:
        return jsonify({'error': 'Bucket name and object key are required'}), 400

    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=credentials.get('access_key'),
            aws_secret_access_key=credentials.get('secret_access_key'),
            region_name='ap-south-1'
        )

        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=3600*12
        )

        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

app.run(debug=True)
