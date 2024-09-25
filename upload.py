import os
import hashlib
import requests
import logging

# CONFIGURATION
API_URL_BASE = 'https://api.laposte.fr/digiposte/v3/partner/safes/PCA_'
FOLDER_ID = '16c3a384bd574c039290b51739f339b5'

DIRECTORY_PATH = r'\\groupevsc.com\share\PCA\Documentation critique commune\Direction Tech\CSI et ODQ\Scripts\ScriptAZAD_1-3O'
HEADERS = {
    'Authorization': 'Bearer c31a27c3-a6d8-4139-bd19-7e5688c9ab92',
    'X-Okapi-Key': 'LUwqbDs5ENNTMpt4TeTORtcyD4j8lgwiK7LZt7DEQhPUuESEgGJ5dy95z9bPadG/',  
    'Accept': '*/*',
    'User-Agent': 'PostmanRuntime/7.40.0',
}

LOG_FILE = 'uploaded_files.log'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()



def load_uploaded_files(log_file):
   
    if not os.path.exists(log_file):
        return set()
    
    with open(log_file, 'r') as f:
        return set(line.strip() for line in f)
    


def save_uploaded_file(log_file, file_hash):
  
    with open(log_file, 'a') as f:
        f.write(f"{file_hash}\n")



def upload_file(file_path, folder_id, uploaded_files):
    try:
        file_hash = calculate_sha256(file_path)

        
        if file_hash in uploaded_files:
            logging.info(f"File already uploaded, skipping: {os.path.basename(file_path)}")
            return
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        if file_name in ['.DS_Store', 'Thumbs.db'] or file_name.startswith('._'):
            logging.warning(f"Skipping system file: {file_name}")
            return
        with open(file_path, 'rb') as file:
            files = {
                'title': (None, file_name),
                'health': (None, 'false'),
                'hash': (None, file_hash),
                'size': (None, str(file_size)),
                'filename': (file_name, file, 'application/octet-stream')  
            }

            logging.info(f"Uploading file: {file_name} to folder ID: {folder_id}")

            upload_url = f'{API_URL_BASE}/documents?folder_id={folder_id}'
            response = requests.post(upload_url, headers=HEADERS, files=files)

            if response.status_code == 200:
                logging.info(f'Successfully uploaded {file_name}')
                save_uploaded_file(LOG_FILE, file_hash) 
            else:
                logging.error(f'Failed to upload {file_name}. Status code: {response.status_code}')
                logging.error('Response: %s', response.json())
    except requests.exceptions.RequestException as e:
        logging.error(f'Network error occurred while uploading file {file_path}: {e}')
    except Exception as e:
        logging.error(f'Error uploading file {file_path}: {e}')



def process_directory(root_dir, folder_id):
    try:
        uploaded_files = load_uploaded_files(LOG_FILE)
        files = os.listdir(root_dir)
        for file_name in files:
            file_path = os.path.join(root_dir, file_name)
            if os.path.isfile(file_path):
                upload_file(file_path, folder_id, uploaded_files)
    except Exception as e:
        logging.error(f'Error processing directory {root_dir}: {e}')

if __name__ == "__main__":
    process_directory(DIRECTORY_PATH, FOLDER_ID)
