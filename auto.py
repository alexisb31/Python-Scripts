import os
import hashlib
import logging
import requests
from datetime import datetime
from base64 import b64encode

API_URL_BASE = 'https://api.laposte.fr/digiposte/v3/partner/safes/PCA_'
TOKEN_URL = 'https://api.laposte.fr/digiposte/v3/oauth/token'
CLIENT_ID = 'sncf-pca'  
CLIENT_SECRET = 'G4pCAy6Vp9i8'  
DIRECTORY_PATH = r'\\groupevsc.com\share\PCA'
LOG_FILE = 'uploaded_files.log'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_token():
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = b64encode(auth_str.encode()).decode()
    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials'
    }
    logging.info(f"Requesting token with headers: {headers} and data: {data}")
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    logging.info(f"Response Status Code: {response.status_code}")
    logging.info(f"Response Text: {response.text}")
    if response.status_code == 200:
        token = response.json().get('access_token')
        logging.info(f"Token generated successfully: {token}")
        return token
    else:
        logging.error(f"Failed to generate token: {response.status_code} - {response.text}")
        return None

def get_headers():
    token = get_token()
    if token:
        return {
            'Authorization': f'Bearer {token}',
            'X-Okapi-Key': 'LUwqbDs5ENNTMpt4TeTORtcyD4j8lgwiK7LZt7DEQhPUuESEgGJ5dy95z9bPadG/',  
            'Accept': '*/*',
            'User-Agent': 'PostmanRuntime/7.40.0',
        }
    else:
        return None

def get_file_modification_date(file_path):
    return datetime.fromtimestamp(os.path.getmtime(file_path))

def get_local_files(directory_path):
    file_tree = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, directory_path)
            file_tree[relative_path] = get_file_modification_date(file_path)
    return file_tree

def get_uploaded_files(folder_id):
    headers = get_headers()
    if not headers:
        return {}
    url = f"{API_URL_BASE}{folder_id}/documents"
    response = requests.get(url, headers=headers)
    logging.info(f"URL: {url}")
    logging.info(f"Headers: {headers}")
    logging.info(f"Response Status Code: {response.status_code}")
    logging.info(f"Response Text: {response.text}")
    if response.status_code == 200:
        return {file['filename']: datetime.strptime(file['last_modified'], '%Y-%m-%dT%H:%M:%S.%fZ') for file in response.json()}
    else:
        logging.error(f"Erreur récupération dossier {folder_id}: {response.status_code} - {response.text}")
        return {}

def compare_trees(local_tree, api_tree):
    changes = {
        'to_add': [],
        'to_update': [],
        'to_delete': []
    }

    for file_name, local_date in local_tree.items():
        if file_name not in api_tree:
            changes['to_add'].append(file_name)
        elif local_date > api_tree[file_name]:
            changes['to_update'].append(file_name)

    for file_name in api_tree:
        if file_name not in local_tree:
            changes['to_delete'].append(file_name)

    return changes

def delete_file_from_api(filename, folder_id):
    headers = get_headers()
    if not headers:
        return
    url = f"{API_URL_BASE}{folder_id}/documents/{filename}"
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        logging.info(f"Fichier supprimé avec succès: {filename}")
    else:
        logging.error(f"Erreur suppression fichier {filename}: {response.status_code} - {response.text}")

def upload_file(file_path, folder_id):
    headers = get_headers()
    if not headers:
        return
    filename = os.path.basename(file_path)
    if not filename:
        logging.error(f"Le fichier n'a pas de nom: {file_path}")
        return
    if filename.lower().endswith(('.db', '.ds_store')):
        logging.info(f"Upload bloqué pour le fichier: {filename}")
        return
    url = f"{API_URL_BASE}{folder_id}/documents"
    files = {'file': (filename, open(file_path, 'rb'))}
    data = {'filename': filename, 'health': False}  # Correction du paramètre 'health' en booléen avec la valeur False
    response = requests.post(url, headers=headers, files=files, data=data)
    if response.status_code == 201:
        logging.info(f"Fichier uploadé avec succès: {filename}")
    else:
        logging.error(f"Erreur upload fichier {filename}: {response.status_code} - {response.text}")

def apply_changes(changes, folder_id):
    for file_name in changes['to_add']:
        file_path = os.path.join(DIRECTORY_PATH, file_name)
        upload_file(file_path, folder_id)
    
    for file_name in changes['to_update']:
        file_path = os.path.join(DIRECTORY_PATH, file_name)
        upload_file(file_path, folder_id)
    
    for file_name in changes['to_delete']:
        delete_file_from_api(file_name, folder_id)

def sync_files(directory_path, folder_id):
    local_tree = get_local_files(directory_path)
    api_tree = get_uploaded_files(folder_id)
    changes = compare_trees(local_tree, api_tree)
    apply_changes(changes, folder_id)

if __name__ == "__main__":
    sync_files(DIRECTORY_PATH, folder_id="095de81fe2fb4cc48a8f2f790867a6f2")