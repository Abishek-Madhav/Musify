import os
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from tempfile import NamedTemporaryFile

# Load the service account JSON from the environment variable
service_account_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')

if not service_account_json:
    raise ValueError("The 'GOOGLE_APPLICATION_CREDENTIALS_JSON' environment variable is not set.")

try:
    # Create a temporary file to store the service account JSON
    with NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
        temp_file.write(service_account_json)
        temp_file_path = temp_file.name

    # Initialize Firebase Admin SDK using the temporary file
    cred = credentials.Certificate(temp_file_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://musify-2ad60-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

finally:
    # Ensure the temporary file is deleted after initialization
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
