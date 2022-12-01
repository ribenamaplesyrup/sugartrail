from requests.auth import HTTPBasicAuth
import requests
import pandas as pd
import sys
from IPython.display import clear_output
import time
import collections
from datetime import datetime
import math
access_token = "829952e2-23ab-44ab-b6e3-efb57f2fceb7"
username = access_token
password = ""
size = "5000"
basic = HTTPBasicAuth(username, password)

def get_appointments(officer_id):
    url = "https://api.company-information.service.gov.uk/officers/" + officer_id + "/appointments?size=" + size
    response = requests.get(url, auth=basic)
    # print metadata
    df = pd.DataFrame(response.json()['items'])
    appointments = len(df)
    print(str(appointments) + " appointments")
    print(str(appointments - df["resigned_on"].count()) + " active appointments")
    return response.json()

def get_locations(companies, address_type: str):
    df = pd.DataFrame(companies['items'])
    if address_type == "correspondance":
        postcode = [address['postal_code'] for address in df['address']]
        addresses = [address['premises'] + ", " + address['address_line_1'] + ", " + address['locality'] + ", " + address['country'] + ", " + address['postal_code'] for address in df['address']]
    elif address_type == "registered":
        addresses = []
        keys = ["address_line_1","address_line_2","country","locality","postal_code"]
        for link in df['links']:
            url = "https://api.company-information.service.gov.uk" + link['company'] + "/registered-office-address"
            response = requests.get(url, auth=basic)
            address = []
            postcode = []
            for key in keys:
                if key in response.json():
                    address += [response.json()[key]]
                    if key == "postal_code":
                        postcode += [response.json()[key]]
            address = ", ".join(address)
            addresses += [address]
    else:
        print("unrecognised address type: should be either corresponance or registered")
        return None
    postcode_frequency = dict(collections.Counter(postcode).items(), key=lambda item: item[1], reverse=True)
    print(str(len(postcode_frequency)) + " unique postcodes")
    frequency = dict(sorted(collections.Counter(addresses).items(), key=lambda item: item[1], reverse=True))
    print(str(len(frequency)) + " unique " + address_type + " addresses")
    print(frequency)
    return addresses

def year_of_creation(companies):
    years = [address['date_of_creation'][0:4] for address in companies]
    frequency = collections.Counter(years)
    return dict(sorted(frequency.items(), key=lambda item: item[1], reverse=True))

def age(creation: str, cessation: str):
    delta = datetime.strptime(cessation, "%Y-%m-%d")-datetime.strptime(creation, "%Y-%m-%d")
    return math.floor(delta.days/365)


def get_companies(addresses):
    companies = {}
    companies_summary = {}
    for address in addresses:
        url = "https://api.company-information.service.gov.uk/advanced-search/companies?location=" + address + "&size=" + size
        response = requests.get(url, auth=basic)
        if response.status_code == 200:
            companies[address] = response.json()['items']
            companies_summary[address] = {}
            companies_summary[address]["frequency"] = response.json()['hits']
            all_companies = [address for address in response.json()['items']]
            active_companies = [address for address in response.json()['items'] if address['company_status'] == 'active']
            dead_companies = [address for address in response.json()['items'] if address['company_status'] == 'dissolved']
            companies_summary[address]["active_companies"] = len(active_companies)
            years = year_of_creation(all_companies)
            survival_months = [age(address['date_of_creation'],address['date_of_cessation']) for address in dead_companies]
            survival_frequency = collections.Counter(survival_months)
            survival_frequency = dict(sorted(survival_frequency.items(), key=lambda item: item[1], reverse=True))
            active_years = year_of_creation(active_companies)
            companies_summary[address]["3_years_active"] = {k: active_years[k] for k in list(active_years)[:3]}
            companies_summary[address]["3_years_all"] = {k: years[k] for k in list(years)[:3]}
            companies_summary[address]["3_survival"] = {k: survival_frequency[k] for k in list(survival_frequency)[:3]}
    companies_summary = dict(sorted(companies_summary.items(), key=lambda item: item[1]["frequency"],reverse=True))
    for i,company in enumerate(companies_summary):
        print("Index: " + str(i))
        print(company)
        print(str(companies_summary[company]['frequency']) + " companies registered or corresponding here, " + str(companies_summary[company]['active_companies']) + " are active.")
        keys = list(companies_summary[company]['3_years_active'].keys())
        life_keys = list(companies_summary[company]['3_survival'].keys())
        for key in keys:
            print(str(companies_summary[company]['3_years_active'][key]) + " currently active companies registered in " + str(key))
        for key in life_keys:
            print(str(companies_summary[company]['3_survival'][key]) + " companies dissolved between years " + str(key+1) + "-" + str(key))
        print("")

    return {key: companies[key] for key in companies_summary if key in companies}

def get_officers(company_locations, indices):
    officers = {}
    for index in indices:
        # get businesses at location
        company_name = list(company_locations.keys())[index]
        officers[str(company_name)] = []
        companies = company_locations[company_name]
        length = len(companies)
        for i, business in enumerate(companies):
            company_number = business['company_number']
            url = "https://api.company-information.service.gov.uk/company/" + company_number + "/officers?size=" + size
            while True:
                try:
                    clear_output(wait=True)
                    print("completion: " + str(100*i/length) + ", index:" + str(i))
                    leadership = requests.get(url, auth=basic)
                    print(leadership)
                    if leadership.json():
                        officers[str(company_name)] += [[officer['name'] for officer in leadership.json()['items']]]
                        clear_output(wait=True)
                        time.sleep(0.41)
                        break
                    else:
                        officers[str(company_name)] += [[]]
                        clear_output(wait=True)
                        time.sleep(0.41)
                        break
                except:
                    print(sys.exc_info()[0])
                    print("taking a 10 second timeout")
                    time.sleep(10)
    clear_output(wait=True)
    for location in list(officers.keys()):
        directors = []
        for business in officers[location]:
            directors += business
        frequency = collections.Counter(directors)
        frequency = dict(sorted(frequency.items(), key=lambda item: item[1], reverse=True))
        print(location)
        print("-")
        print("Most prolific officers:")
        for officer in list(frequency):
            print(str(officer) + " runs " + str(frequency[str(officer)]) + " businesses")
        print("")
    return officers
