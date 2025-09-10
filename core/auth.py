import base64
import certifi
import requests

def get_api_key(config):
    """Get API key using OAuth2 flow"""
    url = "https://id.cisco.com/oauth2/default/v1/token"
    payload = "grant_type=client_credentials"
    
    value = base64.b64encode(
        f"{config.llm.client_id}:{config.llm.client_secret}".encode("utf-8")
    ).decode("utf-8")
    
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {value}",
    }
    
    token_response = requests.post(
        url, headers=headers, data=payload, verify=certifi.where()
    )
    
    if token_response.status_code != 200:
        raise Exception(f"Failed to get API key: {token_response.status_code} - {token_response.text}")
    
    return token_response.json()["access_token"]
