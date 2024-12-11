import requests
def get_user_wallet_nfts(user_address:str):
        print(user_address)
        url = "https://stokenet.radixdlt.com/state/entity/details"
        data = {
          "addresses": [
              user_address
          ]
        }

        # Send a POST request with the JSON dataxs
        response = requests.post(url, json=data)
        user_fungible_resource_arr = []
        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            print(response_data)
            assets = response_data['items'][0]
            user_fungible_resource = assets['fungible_resources']
            user_non_fungible_resource = assets['non_fungible_resources']
            for data in  user_fungible_resource['items']:
                user_fungible_resource_arr.append(data['resource_address'])
            # call api to load all fungible resources
            print('till this works')
            if len(user_fungible_resource_arr) > 20:
                chunk_size = 19
                response = []
                for i in range(0, len(user_fungible_resource_arr), chunk_size):
                    chunk = user_fungible_resource_arr[i:i + chunk_size]
                    resp = collect_asset_from_resource_array(chunk)
                    response.extend(resp)
                return response
            else:
                resp = collect_asset_from_resource_array(user_fungible_resource_arr)
            return resp
        else:
            print("1")
            pass



def collect_asset_from_resource_array(user_fungible_resource_arr:list):

        url = "https://stokenet.radixdlt.com/state/entity/details"
        data = {
            "addresses": user_fungible_resource_arr
        }
        response = requests.post(url, json=data)
        response_data = response.json()
        print(response_data)
        if response.status_code == 200:
            print('line 44')
            response_data = response.json()
            print(response_data)
            assets = response_data['items']
            asset_details = []
            for item in assets:
                resource_address = item['address']
                metadata = item['metadata']['items']
                name = ''
                icon_url = ''
                for data in metadata:
                    try:
                        if data['key'] == 'name':
                            name = data['value']['programmatic_json']['fields'][0]['value']
                        elif data['key'] == 'icon_url':
                            icon_url = data['value']['programmatic_json']['fields'][0]['value']
                    finally:
                        continue
                asset_details.append({
                        'name': name,
                        'icon_url': icon_url,
                        'resource_address':resource_address
                    })
            return asset_details
        else:
            print("3")
            pass


def get_asset_details(fungible_resource: str):
    url = "https://stokenet.radixdlt.com/state/entity/details"
    data = {
        "addresses": [fungible_resource]
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        response_data = response.json()
        assets = response_data['items']
        asset_details = []
        for item in assets:
            resource_address = item['address']
            metadata = item['metadata']['items']
            name = ''
            icon_url = ''
            for data in metadata:
                try:
                    if data['key'] == 'name':
                        name = data['value']['programmatic_json']['fields'][0]['value']
                    elif data['key'] == 'icon_url':
                        icon_url = data['value']['programmatic_json']['fields'][0]['value']
                finally:
                    continue
            asset_details.append({
                'name': name,
                'icon_url': icon_url,
                'resource_address': resource_address
            })
        return asset_details[0]
    else:
        print("3")
        pass

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f'{parent_key}{sep}{k}' if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, subitem in enumerate(v):
                items.extend(flatten_dict({f'{i}': subitem}, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)