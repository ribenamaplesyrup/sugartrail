from sugartrail import api
import requests
import pandas as pd
import random
import urllib
import regex as re

def infer_postcode(address_string):
    postcode = re.findall(r'\b[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}\b', address_string)
    if postcode:
        return postcode[0]
    else:
        return

def load_company_data(company_data_filepath):
    try:
        company_data = pd.read_csv(company_data_filepath)
        return company_data
    except:
        return

def get_nearby_postcode(postcode_string):
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
    address = urllib.parse.quote(address_string)
    url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(address) +'?format=json'
    response = requests.get(url).json()
    if response:
        return {'lat': response[0]['lat'], 'lon': response[0]['lon'], 'address': address_string}
    else:
        postcode_string = infer_postcode(address_string)
        if postcode_string:
            url = "http://api.postcodes.io/postcodes/" + urllib.parse.quote(postcode_string)
            response = requests.get(url).json()
            if str(response['status']) == '200':
                return {'lat': response['result']['latitude'], 'lon': response['result']['longitude'], 'postcode': postcode_string}
            else:
                # try nearby postcode:
                nearby_postcode = get_nearby_postcode(postcode_string)
                if nearby_postcode:
                    url = "http://api.postcodes.io/postcodes/" + urllib.parse.quote(nearby_postcode)
                    response = requests.get(url).json()
                    if str(response['status']) == "200":
                        return {'lat': response['result']['latitude'], 'lon': response['result']['longitude'], 'postcode': nearby_postcode}
                else:
                    print("failed")
        else:
            print("No postcode found for: " + address_string)

def normalise_name(name):
    name_list = name.replace(',','').split(" ")
    name_list.append(name_list.pop(0))
    return ' '.join(name_list)

def process_address_changes(address_changes):
    for i in reversed(range(1,len(address_changes['items']))):
        if 'new_address' not in address_changes['items'][i]['description_values'].keys():
            if 'old_address' in address_changes['items'][i-1]['description_values'].keys():
                address_changes['items'][i]['description_values']['new_address'] = address_changes['items'][i-1]['description_values']['old_address']
    return address_changes

def build_address_history(company_id):
    company_info = api.get_company(company_id)
    company_info_subset = {k:company_info[k] for k in ("date_of_creation","date_of_cessation","registered_office_address") if k in company_info}
    address_changes = api.get_address_changes(company_id)
    address_keys = ('start_date','end_date','address')
    if address_changes['items']:
        address_changes = process_address_changes(address_changes)
        addresses = []
        entry = {}
        entry["company_number"] = str(company_id)
        entry["address"] = str(normalise_address(company_info_subset['registered_office_address']))
        entry["start_date"] = str(address_changes['items'][0]['date'])
        if 'date_of_cessation' in company_info_subset:
            entry["end_date"] = str(company_info_subset['date_of_cessation'])
        else:
            entry["end_date"] = None
        addresses.append(entry)
        for i,change in enumerate(address_changes['items']):
            entry = {}
            entry["company_number"] = str(company_id)
            if 'old_address' in change['description_values']:
                entry["address"] = change['description_values']['old_address']
            else:
                entry["address"] = ""
            if i+1 < len(address_changes['items']):
                entry["start_date"] = str(address_changes['items'][i+1]['date'])
            else:
                entry["start_date"] = company_info_subset['date_of_creation']
            entry["end_date"] = str(change['date'])
            addresses.append(entry)
        return addresses
    else:
        address_history = []
        entry = {}
        for k, key in enumerate(["date_of_creation","date_of_cessation","registered_office_address"]):
            if key in company_info:
                entry[address_keys[k]] = company_info[key]
            else:
                entry[address_keys[k]] = None
        entry["company_number"] = str(company_id)
        entry['address'] = normalise_address(entry['address'])
        return [entry]

def normalise_address(address_dict):
    address_list = []
    for key in ['premises','address_line_1', 'locality','postal_code', 'country']:
                if key in address_dict:
                    address_list.append(address_dict[key])
    address_string = ' '.join(address_list)
    return address_string
