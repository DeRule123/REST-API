import requests
import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()
def get_new_access_token():
    refresh_token = os.getenv("REFRESH_TOKEN")
    offers_uri_root = os.getenv("OFFERS_MICROSERVICE_URI")
    headers = {"Bearer": refresh_token}
    url = offers_uri_root + 'auth'
    response = requests.post(url, headers=headers)

    if response.status_code == 201:
        print("Obtained token")
        return response.json()['access_token']
    
    else:
        print("unable to get token")
        return None


def register_product(url, json_data, prod_header):
    response = requests.post(url, json=json_data, headers=prod_header)

    return response
