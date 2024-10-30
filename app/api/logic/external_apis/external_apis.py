import requests
def get_price_conversion(amount, convert_to):
    url = "https://pro-api.coinmarketcap.com/v2/tools/price-conversion"
    headers = {
        'X-CMC_PRO_API_KEY': '341866e0-5b4a-460f-b2c6-3aee51bbd5cf',
    }
    params = {
        'amount': amount,
        'symbol': 'XRD',
        'convert': convert_to
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        resp = response.json()
        return extract_price(resp, convert_to)
    else:
        response.raise_for_status()


def extract_price(response_json, convert_to):
    try:
        data = response_json['data']
        if data:
            quote = data[0]['quote']
            if convert_to in quote:
                price = quote[convert_to]['price']
                return price
            else:
                raise KeyError(f"Currency {convert_to} not found in the response.")
        else:
            raise KeyError("No data found in the response.")
    except KeyError as e:
        print(f"Error: {e}")
        return None