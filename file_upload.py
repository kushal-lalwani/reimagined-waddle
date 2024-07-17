import os
from flask import Flask, request, jsonify
from utils import upload_to_s3,store_metadata
from postgres_config import connect_to_db

app = Flask(__name__)

UPLOAD_FOLDER = 'Uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@app.post('/upload')
def get_file_paths():
    files = request.files.getlist('files')
    ids = request.form.getlist('ids')
    uploaded_files = []

    if len(files) != len(ids):
        return jsonify({"error": "Number of files and IDs must match"}), 400

    conn = connect_to_db()

    for file, file_id in zip(files, ids):
        if file.filename == '':
            continue
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        upload_to_s3(file_path, file_id)
        store_metadata(conn, file_path,file_id)
        uploaded_files.append({"id": file_id, "filename": file.filename})

        # os.remove(file_path)

    conn.close()
    return jsonify({"message": "Files uploaded successfully", "files": uploaded_files})

app.run(debug=True)
