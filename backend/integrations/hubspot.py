# slack.py
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime
from typing import List
import httpx
import asyncio
import base64
import requests
from integrations.integrationItem import IntegrationItems

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

CLIENT_ID ='9e67aa90-850a-466d-8df7-ae1ce43ea0c1'
CLIENT_SECRET = '6b28b939-7857-4c57-a76a-65c97b87f119'
encoded_client_id_secret = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
authorization_uri='https://app.hubspot.com/oauth/authorize?client_id=9e67aa90-850a-466d-8df7-ae1ce43ea0c1&redirect_uri=http://localhost:8000/integrations/hubspot/oauth2callback&scope=oauth%20crm.objects.companies.read%20crm.objects.deals.read%20crm.objects.contacts.read'
async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)
    return f'{authorization_uri}&state={encoded_state}'

async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(encoded_state)

    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')

    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    async with httpx.AsyncClient() as client:
        form_data = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'code': code,
        }
        
        response, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data=form_data, 
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )

    print(response)  
    print(response.text)  
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    print("credentials in get_hubspot_credentials",credentials)
    return credentials

def create_integration_item_metadata_object(response_json: dict, item_type: str) -> IntegrationItems:
    """Creates an IntegrationItem object from HubSpot API response."""
    return IntegrationItems(
        id=response_json.get('id'),
        type=item_type, 
        createdate=datetime.strptime(response_json['properties'].get('createdate'), '%Y-%m-%dT%H:%M:%S.%fZ')
        if response_json.get('properties', {}).get('createdate') else None,
        email=response_json['properties'].get('email'),
        firstname=response_json['properties'].get('firstname'),
        lastname=response_json['properties'].get('lastname'),
        hs_object_id=response_json['properties'].get('hs_object_id'),
        lastmodifieddate=datetime.strptime(response_json['properties'].get('lastmodifieddate'), '%Y-%m-%dT%H:%M:%S.%fZ')
        if response_json.get('properties', {}).get('lastmodifieddate') else None,
        createdAt=datetime.strptime(response_json.get('createdAt'), '%Y-%m-%dT%H:%M:%S.%fZ')
        if response_json.get('createdAt') else None,
        updatedAt=datetime.strptime(response_json.get('updatedAt'), '%Y-%m-%dT%H:%M:%S.%fZ')
        if response_json.get('updatedAt') else None,
        archived=response_json.get('archived'),
        amount=float(response_json['properties'].get('amount'))
        if response_json['properties'].get('amount') else None,
        closedate=datetime.strptime(response_json['properties'].get('closedate'), '%Y-%m-%dT%H:%M:%S.%fZ')
        if response_json['properties'].get('closedate') else None,
        dealname=response_json['properties'].get('dealname'),
        dealstage=response_json['properties'].get('dealstage'),
        pipeline=response_json['properties'].get('pipeline'),
        domain=response_json['properties'].get('domain'),
        name=response_json['properties'].get('name'),
    )


# Function to fetch items from HubSpot
async def get_items_hubspot(credentials: str) -> List[IntegrationItems]:
    """
    Fetches items from HubSpot API and converts them into IntegrationItem objects.
    """
    credentials = json.loads(json.loads(credentials))
    access_token = credentials.get('access_token')
    headers = {'Authorization': f'Bearer {access_token}'}

    base_url = "https://api.hubspot.com"
    endpoints = [
        {"url": f"{base_url}/crm/v3/objects/contacts", "type": "Contact"},
        {"url": f"{base_url}/crm/v3/objects/deals", "type": "Deal"},
        {"url": f"{base_url}/crm/v3/objects/companies", "type": "Company"},
    ]

    list_of_integration_item_metadata = []

    for endpoint in endpoints:
        url = endpoint["url"]
        item_type = endpoint["type"]
        has_more = True
        after = None

        while has_more:
            params = {"limit": 100, "after": after} if after else {"limit": 100}
            response = requests.get(url, headers=headers, params=params)
            print("response1233",response.json())
            if response.status_code == 200:
                response_json = response.json()
                results = response_json.get("results", [])
                for result in results:
                    list_of_integration_item_metadata.append(
                        create_integration_item_metadata_object(result, item_type)
                    )
                has_more = response_json.get("paging", {}).get("next", {}).get("after") is not None
                after = response_json.get("paging", {}).get("next", {}).get("after")
            else:
                print(f"Error fetching {item_type}s: {response.status_code} - {response.text}")
                has_more = False

    print(f"Fetched {len(list_of_integration_item_metadata)} items from HubSpot.")
    return list_of_integration_item_metadata