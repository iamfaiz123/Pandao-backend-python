import requests
def get_user_wallet_nfts(user_address:str):
        url = "https://stokenet.radixdlt.com/state/entity/details"
        data = {
          "addresses": [
            "account_tdx_2_129qvh025nwetpnq0dlajlzcffw0vahdw9x2zqn04edwnp4sgw93m5m"
          ]
        }

        # Send a POST request with the JSON dataxs

        response = requests.post(url, json=data)

        user_fungible_resource_arr = []
        user_non_fungible_resource_arr = []

        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            assets = response_data['items'][0]
            user_fungible_resource = assets['fungible_resources']
            user_non_fungible_resource = assets['non_fungible_resources']
            for data in  user_fungible_resource['items']:
                user_fungible_resource_arr.append(data['resource_address'])
            # call api to load all fungible resources
            print('till this works')
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
        if response.status_code == 200:
            response_data = response.json()
            assets = response_data['items']
            asset_details = []
            for item in assets:
                resource_address = item['address']
                metadata = item['metadata']['items']
                assets_metadata = []
                for data in metadata:
                    try:
                        assets_metadata.append(
                            {
                                data['key'] : data['value']['programmatic_json']['fields'][0]['value'],
                                'address' : resource_address
                            }
                        )
                    finally:
                        continue
                asset_details.append(assets_metadata)
            return asset_details
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