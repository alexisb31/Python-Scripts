import os
import requests
import logging
import pandas as pd

# CONFIGURATION
API_URL_BASE = 'https://api.laposte.fr/digiposte/v3/partner/safes/PCA_/folders/' 
HEADERS = {
   'Authorization': 'Bearer 0c8cce58-ec7b-4fb3-aa1c-5ff7a05bb5ef',
    'X-Okapi-Key': 'LUwqbDs5ENNTMpt4TeTORtcyD4j8lgwiK7LZt7DEQhPUuESEgGJ5dy95z9bPadG/',
    'Accept': '*/*',
    'User-Agent': 'PostmanRuntime/7.40.0',
}

FILE_NAME = 'liste_dossierAPIDGP.xlsx'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_folders_recursively(folder_id):

    
    folders_info = []
    url = f"{API_URL_BASE}{folder_id}"

    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        folders = data.get('folders', [])
        
        #déclaration valeur avant récur fonction

        for folder in folders:
            folder_id = folder['folder_id']
            folder_name = folder['name']
            folders_info.append({'ID': folder_id, 'Name': folder_name})

            # appel récursif de la fonction

            folders_info.extend(get_folders_recursively(folder_id))
    else:
        logging.error(f"Failed to retrieve folders. Status code: {response.status_code}")
        logging.error(f"Response: {response.json()}")
    
        

    return folders_info

def save_to_excel(folders_info):

    if os.path.exists(FILE_NAME):
    
        existing_df = pd.read_excel(FILE_NAME)
       
        new_df = pd.DataFrame(folders_info)

        new_df = new_df[~new_df['ID'].isin(existing_df['ID'])]
     
        combined_df = pd.concat([existing_df, new_df]).drop_duplicates().reset_index(drop=True)
    else:
    
        combined_df = pd.DataFrame(folders_info)

    combined_df.to_excel(FILE_NAME, index=False)
    logging.info(f"Data saved to {FILE_NAME}")

if __name__ == "__main__":
   
    root_folder_id = "abc6038f587c4a1cb976ead7e7e65a31"  
    folders_info = get_folders_recursively(root_folder_id)
    if folders_info:
        save_to_excel(folders_info)