import collections
import regex as re
import requests
import urllib
import os
import datetime
import requests

def download_file(url, folder_path):
    # Ensure the folder exists, create if it doesn't
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Extract the filename from the URL
    filename = url.split('/')[-1]
    file_path = os.path.join(folder_path, filename)

    # Download the file
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"File downloaded successfully: {file_path}")
        return file_path
    else:
        print(f"Failed to download file: HTTP {response.status_code}")

def get_first_day_of_current_month():
    # Get the current date
    today = datetime.date.today()
    # Create a new date object for the first day of the current month
    first_day = datetime.date(today.year, today.month, 1)
    # Return the first day in the format YYYY-MM-DD
    return first_day.strftime('%Y-%m-%d')

def ensure_json_extension(filename):
    # Check if the filename ends with '.json'
    if filename.endswith('.json'):
        return filename
    else:
        # Remove the current extension if there is one
        filename_without_ext = os.path.splitext(filename)[0]
        # Append '.json' to the filename
        return filename_without_ext + '.json'

def flatten(d, parent_key='', sep='.'):
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def normalise_name(name):
    """Move first word (often surname) from the beginning to the end of string."""
    name_list = name.replace(',','').split(" ")
    name_list.append(name_list.pop(0))
    return ' '.join(name_list)

def normalise_address(address_dict):
    """Joins address key values into a single str."""
    address_list = []
    for key in ['premises','address_line_1', 'locality','postal_code', 'country']:
                if key in address_dict:
                    address_list.append(address_dict[key])
    address_string = ' '.join(address_list)
    return address_string

def infer_postcode(address_string):
    """Extracts UK postcode from input address string with regex."""
    postcode = re.findall(r'\b[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}\b', address_string)
    if postcode:
        return postcode[0]
    else:
        return

def get_nearby_postcode(postcode_string):
    """Find closest nearby postcode to input postcode (postcode_string)."""
    url = "http://api.postcodes.io/postcodes/" + postcode_string[:-1] + "/autocomplete"
    response = requests.get(url).json()
    if response['result'] != None:
        closest_address = {}
        for postcode in response["result"]:
            distance = abs(ord(postcode[-1]) - ord(postcode_string[-1]))
            if closest_address:
                if distance < closest_address["distance"]:
                    closest_address = {"postcode": postcode, "distance": distance}
            else:
                closest_address = {"postcode": postcode, "distance": distance}
        return closest_address["postcode"]

def get_coords_from_address(address_string):
    """Attempt retrieval of coords for input address string."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    try:
        # Nominatim API request
        params = {'q': address_string, 'format': 'json'}
        url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(params)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        if response.status_code == 200 and response.text:
            response_json = response.json()
            if response_json:
                return {'lat': response_json[0]['lat'], 'lon': response_json[0]['lon'], 'address': address_string}
            else:
                # If Nominatim fails, try with postcode.io
                postcode_string = infer_postcode(address_string)
                if postcode_string:
                    url = "http://api.postcodes.io/postcodes/" + urllib.parse.quote(postcode_string)
                    response = requests.get(url, headers=headers, timeout=10)
                    response_json = response.json()
                    
                    if str(response_json['status']) == '200':
                        return {'lat': response_json['result']['latitude'], 'lon': response_json['result']['longitude'], 'postcode': postcode_string}
                    else:
                        # Try nearby postcode
                        nearby_postcode = get_nearby_postcode(postcode_string)
                        if nearby_postcode:
                            url = "http://api.postcodes.io/postcodes/" + urllib.parse.quote(nearby_postcode)
                            response = requests.get(url, headers=headers, timeout=10)
                            response_json = response.json()
                            
                            if str(response_json['status']) == "200":
                                return {'lat': response_json['result']['latitude'], 'lon': response_json['result']['longitude'], 'postcode': nearby_postcode}
        print("Failed to retrieve coordinates.")
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    
    return None
