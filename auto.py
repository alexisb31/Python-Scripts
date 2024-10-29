import os
import hashlib
import time
import requests
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

API_URL_BASE = 'https://api.laposte.fr/digiposte/v3/partner/safes/PCA_'
FOLDER_ID = '0e8e0d98b6db4cab95a42bec634972b0'
DIRECTORY_PATH = r'\\groupevsc.com\share\PCA'
HEADERS = {
    'Authorization': 'Bearer b9212009-18ad-43eb-905a-4f5c3a80a9d3',
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

def get_uploaded_files(folder_id):
    url = f"{API_URL_BASE}{folder_id}/documents"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return {file['filename']: file['sha256'] for file in response.json()}
    else:
        logging.error(f"Erreur récupération  dossier {folder_id}: {response.status_code} - {response.text}")
        return {}

def upload_file(file_path, folder_id):
    file_hash = calculate_sha256(file_path)
    file_name = os.path.basename(file_path)
    
    uploaded_files = get_uploaded_files(folder_id)
    if file_name in uploaded_files and uploaded_files[file_name] == file_hash:
        logging.info(f"Fichier déjà uploadé: {file_name}")
        return

    url = f"{API_URL_BASE}{folder_id}/documents"
    with open(file_path, 'rb') as file:
        files = {'file': (file_name, file)}
        response = requests.post(url, headers=HEADERS, files=files)
        if response.status_code == 201:
            logging.info(f"Fichier uploadé avec succès: {file_name}")
        else:
            logging.error(f"Erreur upload fichier {file_name}: {response.status_code} - {response.text}")

def delete_item(file_name, folder_id):
    url = f"{API_URL_BASE}{folder_id}/documents/{file_name}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 204:
        logging.info(f"Fichier supprimé avec succès: {file_name}")
    else:
        logging.error(f"Erreur suppression fichier {file_name}: {response.status_code} - {response.text}")

def get_local_file_tree(directory_path):
    file_tree = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_tree[file] = calculate_sha256(file_path)
    return file_tree

def compare_trees(local_tree, api_tree):
    changes = {
        'to_add': [],
        'to_update': [],
        'to_delete': []
    }

    for file_name, file_hash in local_tree.items():
        if file_name not in api_tree:
            changes['to_add'].append(file_name)
        elif file_hash != api_tree[file_name]:
            changes['to_update'].append(file_name)

    for file_name in api_tree:
        if file_name not in local_tree:
            changes['to_delete'].append(file_name)

    return changes

def apply_changes(changes, folder_id):
    for file_name in changes['to_add']:
        file_path = os.path.join(DIRECTORY_PATH, file_name)
        upload_file(file_path, folder_id)
    
    for file_name in changes['to_update']:
        file_path = os.path.join(DIRECTORY_PATH, file_name)
        upload_file(file_path, folder_id)
    
    for file_name in changes['to_delete']:
        delete_item(file_name, folder_id)

if __name__ == "__main__":
    class ChangeHandler(FileSystemEventHandler):
        def on_deleted(self, event):
            file_name = os.path.basename(event.src_path)
            delete_item(file_name, FOLDER_ID)

    observer = Observer()
    event_handler = ChangeHandler()
    observer.schedule(event_handler, DIRECTORY_PATH, recursive=True)
    observer.start()
    logging.info(f"Surveillance du dossier: {DIRECTORY_PATH}")

    try:
        while True:
            local_tree = get_local_file_tree(DIRECTORY_PATH)
            api_tree = get_uploaded_files(FOLDER_ID)
            changes = compare_trees(local_tree, api_tree)
            apply_changes(changes, FOLDER_ID)
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
