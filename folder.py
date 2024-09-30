import os
import requests
import logging

# CONFIG
API_URL_BASE = 'https://api.laposte.fr/digiposte/v3/partner/safes/PCA_'
PARENT_FOLDER_ID = '10ef3576633c4b53b58ea1c62841573b' 
DIRECTORY_PATH = r'\\groupevsc.com\share\PCA\Documentation critique commune\Direction Tech\CSI et ODQ\Scripts\ScriptAD_5-5'
HEADERS = {
    'Authorization': 'Bearer c31a27c3-a6d8-4139-bd19-7e5688c9ab92',
    'X-Okapi-Key': 'LUwqbDs5ENNTMpt4TeTORtcyD4j8lgwiK7LZt7DEQhPUuESEgGJ5dy95z9bPadG/',
    'Accept': '*/*',
    'User-Agent': 'PostmanRuntime/7.40.0',
}


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_folder_on_api(folder_name, parent_folder_id):
    
    try:
       
        url = f'{API_URL_BASE}/folders'
        files = {
            'name': (None, folder_name),
            'parent_folder_id': (None, parent_folder_id)
        }
        response = requests.post(url, headers=HEADERS, files=files)

        if response.status_code == 201: 
            folder_id = response.json().get('id')
            logging.info(f"Successfully created folder: {folder_name} with ID: {folder_id}")
            return folder_id
        else:
            logging.error(f"forced success {folder_name}. Status code: {response.status_code}")
            logging.error('Response: %s', response.json())
    except Exception as e:
        logging.error(f"Error creating folder {folder_name}: {e}")
    return None

def process_directory(root_dir, parent_folder_id):

    try:
        dirs = next(os.walk(root_dir))[1]  

        for directory in dirs:
            folder_name = directory
            logging.info(f"Processing directory: {folder_name}")

            
            current_folder_id = create_folder_on_api(folder_name, parent_folder_id)
            if current_folder_id is None:
                logging.error(f"forced sucess {folder_name}, pass to next folder.")
                continue

    except Exception as e:
        logging.error(f"Error processing directory {root_dir}: {e}")

if __name__ == "__main__":
    process_directory(DIRECTORY_PATH, PARENT_FOLDER_ID)