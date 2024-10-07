import os
import hashlib
import time
import requests
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import folder

# CONFIGURATION
API_URL_BASE = 'https://api.laposte.fr/digiposte/v3/partner/safes/PCA_'
FOLDER_ID = '9188ea8d478d442ab91af4e461923bcf'
DIRECTORY_PATH = r'\\groupevsc.com\share\PCA'
HEADERS = {
    'Authorization': 'Bearer 079ff320-85d2-4550-872e-d33b2ffb695f',
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
        return {file['name']: file['sha256'] for file in response.json()}
    else:
        logging.error(f"Échec de la récupération des fichiers du dossier {folder_id}: {response.status_code} - {response.text}")
        return {}

def create_folder_on_server(folder_name, parent_folder_id):
    url = f"{API_URL_BASE}{parent_folder_id}/folders"
    data = {
        "name": folder_name
    }
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        logging.info(f"Dossier créé avec succès: {folder_name}")
        return response.json()['id']
    else:
        logging.error(f"Échec de la création du dossier {folder_name}: {response.status_code} - {response.text}")
        return None

def upload_file(file_path, folder_id):
    try:
        file_hash = calculate_sha256(file_path)
        file_name = os.path.basename(file_path)

        uploaded_files = get_uploaded_files(folder_id)
        if file_name in uploaded_files and uploaded_files[file_name] == file_hash:
            logging.info(f"Le fichier {file_name} est déjà uploadé.")
            return

        url = f"{API_URL_BASE}/documents?folder_id={folder_id}'"
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(url, headers=HEADERS, files=files)
            if response.status_code == 201:
                logging.info(f"Fichier téléchargé avec succès: {file_name}")
            else:
                logging.error(f"Échec du téléchargement du fichier {file_name}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur réseau lors du téléchargement du fichier {file_path}: {e}")
    except Exception as e:
        logging.error(f"Erreur lors du téléchargement du fichier {file_path}: {e}")

def delete_item(file_path):
    file_name = os.path.basename(file_path)
    url = f"{API_URL_BASE}/documents/{file_name}"
    try:
        response = requests.delete(url, headers=HEADERS)
        if response.status_code == 204:
            logging.info(f"Fichier supprimé avec succès: {file_name}")
        else:
            logging.error(f"Échec de la suppression du fichier {file_name}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur réseau lors de la suppression du fichier {file_path}: {e}")
    except Exception as e:
        logging.error(f"Erreur lors de la suppression du fichier {file_path}: {e}")

    pass


def get_local_file_tree(directory_path):
    file_tree = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_tree[file_path] = calculate_sha256(file_path)
    return file_tree

def compare_trees(local_tree, api_tree):
    changes = {
        'to_add': [],
        'to_update': [],
        'to_delete': []
    }

    for local_path, local_hash in local_tree.items():
        if local_path not in api_tree:
            changes['to_add'].append(local_path)
        elif local_hash != api_tree[local_path]:
            changes['to_update'].append(local_path)

    for api_path in api_tree:
        if api_path not in local_tree:
            changes['to_delete'].append(api_path)

    return changes

def apply_changes(changes, folder_id):
    for file_path in changes['to_add']:
        upload_file(file_path, folder_id)
    for file_path in changes['to_update']:
        upload_file(file_path, folder_id)
    for file_path in changes['to_delete']:
        delete_item(file_path)

class ChangeHandler(FileSystemEventHandler):
    def on_deleted(self, event):
        delete_item(event.src_path)

   

if __name__ == "__main__":
    path = r'\\groupevsc.com\share\PCA'
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"Surveillance du dossier: {path}")

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