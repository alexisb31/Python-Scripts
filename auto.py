import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

API_BASE_URL = "https://api.laposte.fr/digiposte/v3/partner/safes/PCA_"
TOKEN_URL = "https://api.laposte.fr/digiposte/v3/oauth/token"
CLIENT_ID = "sncf-pca" 
CLIENT_SECRET = "G4pCAy6Vp9i8" 


def get_access_token():
    try:
        auth = (CLIENT_ID, CLIENT_SECRET)
        data = {"grant_type": "client_credentials"}
        response = requests.post(TOKEN_URL, auth=auth, data=data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data['access_token']
        else:
            print(f"Erreur lors de l'obtention du token : {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Erreur lors de la requête du token : {e}")
    return None


def api_request(url, method='POST', data=None, files=None):
    token = get_access_token()
    if not token:
        print("Impossible d'obtenir un token, requête annulée.")
        return
    headers = {"Authorization": f"Bearer {token}"}

    try:
        if method == 'POST':
            response = requests.post(url, json=data, files=files, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, json=data, headers=headers)

        return response
    except Exception as e:
        print(f"Erreur lors de la requête API : {e}")
        return None


def create_folder(path):
    url = f"{API_BASE_URL}/create_folder"
    data = {"path": path}
    response = api_request(url, data=data)
    if response and response.status_code == 200:
        print(f"Dossier créé dans l'API: {path}")
    else:
        print(f"Erreur création dossier {path}: {response.text}")


def upload_file(path):
    url = f"{API_BASE_URL}/upload_file"
    try:
        with open(path, 'rb') as f:
            files = {'file': (path, f)}
            response = api_request(url, files=files)
        if response and response.status_code == 200:
            print(f"Fichier uploadé dans l'API: {path}")
        else:
            print(f"Erreur upload fichier {path}: {response.text}")
    except Exception as e:
        print(f"Erreur lecture fichier {path}: {e}")


def delete_item(path):
    url = f"{API_BASE_URL}/delete"
    data = {"path": path}
    response = api_request(url, data=data)
    if response and response.status_code == 200:
        print(f"Élément supprimé dans l'API: {path}")
    else:
        print(f"Erreur suppression élément {path}: {response.text}")

def update_file(path):
    upload_file(path)


class ChangeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            create_folder(event.src_path)
        else:
            upload_file(event.src_path)

    def on_deleted(self, event):
        delete_item(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            update_file(event.src_path)

if __name__ == "__main__":
    path = "\\groupevsc.com\share\PCA"
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"Surveillance du dossier: {path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
