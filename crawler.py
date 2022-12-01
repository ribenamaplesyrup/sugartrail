from requests.auth import HTTPBasicAuth
import requests
import pandas as pd
import sys
from IPython.display import clear_output
import time
import numpy as np
import collections
from datetime import datetime
import math
# from GoogleNews import GoogleNews
import random
access_token = ""
username = access_token
password = ""
size = "5000"
basic = HTTPBasicAuth(username, password)

class Ownership_Network:
    def __init__(self, officer_id=None, company_id=None, address=None):
        self.addresses = pd.DataFrame(columns=['address','n'])
        self.officer_ids = pd.DataFrame(columns=['officer_id','n'])
        self.company_ids = pd.DataFrame(columns=['company_id','n'])
        self.companies = pd.DataFrame(columns=['company_number','n'])
        self.officer_id = officer_id
        self.company_id = company_id
        self.address = address
        self.n = 0
        self.edge = "Origin"
        self.initialise_dataframe()
    
    def initialise_dataframe(self):
        if self.officer_id:
            self.officer_ids = self.officer_ids.append({'officer_id': self.officer_id, 'name': get_appointments(self.officer_id)[0]['name'], 'n':self.n, 'edge':self.edge, 'node': None, 'node_type': 'Person'}, ignore_index=True)
        elif self.company_id:
            self.company_ids = self.company_ids.append({'company_id': self.company_id, 'n':self.n, 'edge':self.edge, 'node': None, 'node_type': 'Company'}, ignore_index=True)
            company = get_company(self.company_id)
            company['n'] = self.n
            company['edge'] = self.edge
            self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)
        elif self.address:
            self.addresses = self.addresses.append({'address': self.address, 'n':self.n, 'edge':self.edge, 'node': None, 'node_type': 'Address'}, ignore_index=True)
        else:
            print("no input provided")

    def search_officer_id(self, officer_id):
        appointments = get_appointments(officer_id)
        self.node_type = "Person"
        self.node = officer_id 
        for appointment in appointments:
            if normalise_address(appointment['address']) not in self.addresses['address'].unique():
                self.edge = "Appointment Address"
                self.addresses = self.addresses.append({'address': normalise_address(appointment['address']), 'n':self.n, 'edge':self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True)
            if appointment['appointed_to']['company_number'] not in self.company_ids['company_id'].unique():
                self.edge = "Appointment"
                self.company_ids = self.company_ids.append({'company_id': appointment['appointed_to']['company_number'], 'n':self.n, 'edge':self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True)
#                 company = get_company(appointment['appointed_to']['company_number'])
#                 company['n'] = self.n
#                 company['edge'] = self.edge
#                 company['node'] = self.node
#                 company['node_type'] = self.node_type
#                 self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)
        correspondance_address = get_correspondance_address(officer_id)
        if normalise_address(correspondance_address) not in self.addresses['address'].unique():
            self.edge = "Officer Corresponance Address"
            self.addresses = self.addresses.append({'address': normalise_address(correspondance_address), 'n':self.n, 'edge':self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True)
        duplicate_officers = get_duplicate_officers(officer_id)
        for duplicate in duplicate_officers:
            self.edge = "Duplicate Officer"
            if duplicate['links']['self'].split('/')[2] not in self.officer_ids['officer_id'].unique():
                self.officer_ids = self.officer_ids.append({'officer_id': duplicate['links']['self'].split('/')[2], 'name': duplicate['title'], 'n':self.n, 'edge': self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True)
    
    def normalise_name(name):
        name_list = name.replace(',','').split(" ")
        name_list.insert(0, name_list.pop())
        return ' '.join(name_list)

    def search_company_id(self, company_id):
        officers = get_officers(company_id)
        self.node_type = "Company"
        self.node = company_id
        if officers:
            for officer in officers:
                if normalise_address(officer['address']) not in self.addresses['address'].unique():
                    self.edge = "Officer Corresponance Address"
                    self.addresses = self.addresses.append({'address': normalise_address(officer['address']), 'n':self.n, 'edge':self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True)
                if officer['links']['officer']['appointments'].split('/')[2] not in self.officer_ids['officer_id'].unique():
                    self.edge = "Officer"
                    self.officer_ids = self.officer_ids.append({'officer_id': officer['links']['officer']['appointments'].split('/')[2], 'name': normalise_name(officer['name']), 'n':self.n, 'edge':self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True)
        psc = get_psc(company_id)
        if psc:
            for person in psc:
                if "address" in person:
                    self.edge = "Person of Significant Control Address"
                    if normalise_address(person['address']) not in self.addresses['address'].unique():
                        self.addresses = self.addresses.append({'address': normalise_address(person['address']), 'n':self.n, 'edge':self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True) 
        address_history = build_address_history(company_id)
        for address in address_history:
            self.edge = "Company Historical Address"
            if address['address'] not in self.addresses['address'].unique():
                self.addresses = self.addresses.append({'address': address['address'], 'n':self.n, 'edge':self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True)  

    def search_address(self, address):
        companies = get_companies_at_address(address)
        self.node_type = "Address"
        self.node = address
        if companies:
            for company in companies:
                self.edge = "Company Address"
                if company['company_number'] not in self.company_ids['company_id'].unique():
                    self.company_ids = self.company_ids.append({'company_id': company['company_number'], 'n':self.n, 'edge':self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True)
#                     company = get_company(company['company_number'])
#                     if company:
#                         company['n'] = self.n
#                         company['edge'] = self.edge
#                         company['node'] = self.node
#                         company['node_type'] = self.node_type
#                         self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)
            officers = get_officers_at_location(address)
            for officer in officers:
                self.edge = "Officer at Address"
                if officer['links']['self'].split('/')[2] not in self.officer_ids['officer_id'].unique():
                    self.officer_ids = self.officer_ids.append({'officer_id': officer['links']['self'].split('/')[2], 'name': officer['title'], 'n':self.n, 'edge':self.edge, 'node': self.node, 'node_type': self.node_type}, ignore_index=True)
    
    def get_company_from_id(self, company_id=None):
        company_list = []
        if company_id:
            if company_id in self.company_ids['company_id'].unique():
                company_list = [company_id]
            else:
                print("add valid company id")
        else:
            company_list = self.company_ids['company_id'].unique()
        for company_id in company_list:
            if company_id not in self.companies['company_number'].unique():
                company = get_company(company_id)
                if company:
                    company['n'] = self.company_ids.loc[self.company_ids['company_id'] == company_id]['n']
                    company['edge'] = self.company_ids.loc[self.company_ids['company_id'] == company_id]['edge']
                    company['node'] = self.company_ids.loc[self.company_ids['company_id'] == company_id]['node']
                    company['node_type'] = self.company_ids.loc[self.company_ids['company_id'] == company_id]['node_type']
                    self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)

    def hop(self, hops):
        for hop in range(hops):
            print("hop: " + str(hop+1))
            self.n += 1
            selected_addresses = self.addresses.loc[self.addresses['n'] == self.n-1]['address']
            selected_companies = self.company_ids.loc[self.company_ids['n'] == self.n-1]['company_id']
            selected_officers = self.officer_ids.loc[self.officer_ids['n'] == self.n-1]['officer_id']
            for i,address in enumerate(selected_addresses):
                self.search_address(address)
                clear_output(wait=True)
                print("Processed " + str(i+1) + "/" + str(len(selected_addresses)) + " addresses")
            for j,company in enumerate(selected_companies):
                self.search_company_id(company)
                clear_output(wait=True)
                print("Processed " + str(j+1) + "/" + str(len(selected_companies)) + " companies")
            for k,officer in enumerate(selected_officers):
                self.search_officer_id(officer) 
                clear_output(wait=True)
                print("Processed " + str(k+1) + "/" + str(len(selected_officers)) + " officers")
    
    def find_path(self, select_company):
        select_row = self.company_ids.loc[self.company_ids['company_id'] == select_company]
        path = []
        self.get_company_from_id(company_id=select_company)
        backlink = self.companies[self.companies["company_number"] == select_company]['company_name'].item() + " (" + select_row['edge'].item() + ") "
        path.insert(0, backlink)
        while True:
            if select_row['node_type'].item() == "Address":
                select_row = self.addresses.loc[self.addresses['address'] == select_row['node'].item()]
                if select_row['edge'].item() == "Origin":
                    path.insert(0, select_row['address'].item() + " ->")
                    break
                else:
                    backlink = select_row['address'].item() + " (" + select_row['edge'].item() + ") " + "->"
                    path.insert(0, backlink)
            elif select_row['node_type'].item() == "Company":
                select_row = self.company_ids.loc[self.company_ids['company_id'] == select_row['node'].item()]
                self.get_company_from_id(company_id=select_row['company_id'].item())
                if select_row['edge'].item() == "Origin":
                    path.insert(0,self.companies[self.companies["company_number"] == select_row['company_id'].item()]['company_name'].item()+ " ->")
                    break
                else:
                    backlink = self.companies[self.companies["company_number"] == select_row['company_id'].item()]['company_name'].item() + " (" + select_row['edge'].item() + ") " + "->"
                    path.insert(0, backlink)
            elif select_row['node_type'].item() == "Person":
                select_row = self.officer_ids.loc[self.officer_ids['officer_id'] == select_row['node'].item()]
                if select_row['edge'].item() == "Origin":
                    path.insert(0, select_row["name"].item() + " ->")
                    break
                else:
                    backlink = str(select_row['name'].item()) + " (" + str(select_row['edge'].item()) + ") " + "->"
                    path.insert(0, backlink)
            else:
                print("error")
                break
        print(' '.join(path))

def get_appointments(officer_id):
    url = "https://api.company-information.service.gov.uk/officers/" + officer_id + "/appointments?size=" + size
    time.sleep(0.5)
    response = requests.get(url, auth=basic)
    # print metadata
    return response.json()['items']
    
def get_correspondance_address(officer_id):
    url = "https://api.company-information.service.gov.uk/officers/" + officer_id + "/appointments?size=" + size
    time.sleep(0.5)
    response = requests.get(url, auth=basic)
    return response.json()['items'][0]['address']

def get_duplicate_officers(officer_id):
    url = "https://api.company-information.service.gov.uk/officers/" + officer_id + "/appointments?size=5000"
    response = requests.get(url, auth=basic)
    officer_data = response.json()
    officer_self_link = response.json()['links']['self']
    name_list = officer_data['name'].replace(',','').split(' ')
    name = " ".join(name_list[1:]) + " " + name_list[0]
    # search officers with same name 
    url = "https://api.company-information.service.gov.uk/search/officers?q=" + name
    try:
        time.sleep(0.5)
        response = requests.get(url, auth=basic)
        # filter offices with same birthday as search query officer
        
        filtered_results = []
        if 'items' in response.json():
            for officer in response.json()['items']:
                if 'date_of_birth' in officer.keys() and 'date_of_birth' in officer_data.keys():
                    if officer['date_of_birth'] == officer_data['date_of_birth'] and officer['links']['self'] != officer_self_link:
                        filtered_results.append(officer)
            return filtered_results
        else:
            return
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)

def get_psc(company_id):
    url = "https://api.company-information.service.gov.uk/company/" + company_id + "/persons-with-significant-control"
    try:
        time.sleep(0.5)
        response = requests.get(url, auth=basic)
        if response.status_code == 200:
            return response.json()['items']
        else:
            return
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)

def get_company(company_id):
    url = "https://api.company-information.service.gov.uk/company/" + company_id 
    try:
        time.sleep(0.5)
        response = requests.get(url, auth=basic)
        if response.status_code == 200:
            return response.json()
        else:
            print(response.status_code)
            return
    except requests.exceptions.RequestException as e: 
        raise SystemExit(e)

def get_address_changes(company_id):
    url = "https://api.company-information.service.gov.uk/company/" + str(company_id) + "/filing-history/?category=address"
    try:
        time.sleep(0.5)
        # test here to see if page has been found 
        response = requests.get(url, auth=basic)
        if response.status_code == 200:
            if 'items' in response.json():
                return response.json()
        else:
            return
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)
        
def get_company_info(company_id):
    url = "https://api.company-information.service.gov.uk/company/" + str(company_id)
    try:
        time.sleep(0.5)
        # test here to see if page has been found 
        response = requests.get(url, auth=basic)
        if response.json():
            return response.json()
        else:
            return
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)

def normalise_name(name):
    name_list = name.replace(',','').split(" ")
    name_list.insert(0, name_list.pop())
    return ' '.join(name_list)
        
def process_address_changes(address_changes):
    # fill in missing new address values:
    for i in reversed(range(1,len(address_changes['items']))):
        if 'new_address' not in address_changes['items'][i]['description_values'].keys():
            if 'old_address' in address_changes['items'][i-1]['description_values'].keys():
                address_changes['items'][i]['description_values']['new_address'] = address_changes['items'][i-1]['description_values']['old_address']
#     df = pd.json_normalize(address_changes['items'])
    return address_changes
        
def build_address_history(company_id):
    company_info = get_company_info(company_id)
    company_info_subset = {k:company_info[k] for k in ("date_of_creation","date_of_cessation","registered_office_address") if k in company_info}
    address_changes = get_address_changes(company_id)
    address_keys = ('start_date','end_date','address')
    if address_changes['items']:
        address_changes = process_address_changes(address_changes)
        ###
        addresses = []
        entry = {}
        entry["address"] = str(normalise_address(company_info_subset['registered_office_address']))
        entry["start_date"] = str(address_changes['items'][0]['date'])
        if 'date_of_cessation' in company_info_subset:
            entry["end_date"] = str(company_info_subset['date_of_cessation'])
        else:
            entry["end_date"] = None
        addresses.append(entry)

        for i,change in enumerate(address_changes['items']):
            entry = {}
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
        entry['address'] = normalise_address(entry['address'])
        return [entry]
    
def normalise_address(address_dict):
    address_list = []
    for key in ['premises','address_line_1', 'locality','postal_code', 'country']:
                if key in address_dict:
                    address_list.append(address_dict[key])
    address_string = ' '.join(address_list)
    return address_string

def get_news(df):
    company_news = []
    full_name_news = []
    short_name_news = []
    searched = {}
    for index, row in df.iterrows():
        time.sleep(random.uniform(0, 1))
        company_name = row['company_name']
        full_name = row['name']
        if type(row["name_elements"]) == dict:
            short_name = '"' + row["name_elements"]["forename"] + " " + row["name_elements"]["surname"] + '"'
        else:
            short_name = '"' + row["name_elements"] + '"'
        # add a check ...
        if company_name in searched:
            company_news.append(searched[company_name])
        else:
            searched[company_name] = company_news_check(company_name)
            company_news.append(searched[company_name])
        if full_name in searched:
            full_name_news.append(searched[full_name])
        else:
            searched[full_name] = company_news_check(full_name)
            full_name_news.append(searched[full_name])
        if short_name in searched:
            short_name_news.append(searched[short_name])
        else:
            searched[short_name] = company_news_check(short_name)
            short_name_news.append(searched[short_name])
        progress = str(int(100*index/len(df)))+"%"
        print(progress)
    df['company_news'] = company_news
    df['full_name_news'] = full_name_news
    df['short_name_news'] = short_name_news
    return df

def company_news_check(search_term):
    time.sleep(random.uniform(0, 0.2))
    googlenews = GoogleNews(period='10y')
    news = []
    googlenews.get_news('"' + str(search_term) + '"')
    for story in googlenews.results():
        if story['title'] not in news:
            news += [story['title']]
    return news

def get_locations(companies, address_type: str):
    df = companies
    if address_type == "correspondance":
        addresses = []
        for address in df['address']:
            address_string_list = []
            for key in ['premises','address_line_1', 'locality', 'country','postal_code']:
                if key in address:
                    address_string_list.append(address[key])
            address_string = ', '.join(address_string_list)
            addresses += [address_string]
    elif address_type == "registered":
        addresses = []
        keys = ["address_line_1","address_line_2","country","locality","postal_code"]
        for link in df['links']:
            url = "https://api.company-information.service.gov.uk" + link['company'] + "/registered-office-address"
            time.sleep(0.5)
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

def remove_company_type(company_name):
    split_name = company_name.split(" ")
    if split_name[-1] in ["LIMITED","LTD","LTD.","PLC","LLP","RTM","CIC","CASC"]:
        return " ".join(split_name[:-1])
    else:
        return company_name

def year_of_creation(companies):
    years = [address['date_of_creation'][0:4] for address in companies]
    frequency = collections.Counter(years)
    return dict(sorted(frequency.items(), key=lambda item: item[1], reverse=True))

def age(creation: str, cessation: str):
    delta = datetime.strptime(cessation, "%Y-%m-%d")-datetime.strptime(creation, "%Y-%m-%d")
    return math.floor(delta.days/365)

def get_companies_at_address(address):
    companies = {}
    companies_summary = {}
    url = "https://api.company-information.service.gov.uk/advanced-search/companies?location=" + address + "&size=" + "50"
    time.sleep(0.5)
    response = requests.get(url, auth=basic)
    if response.status_code == 200:
        # this is what we want in a dataframe:
        return response.json()['items']

def company_summary(df):
    registered_companies = len(df)
    active_companies = df['company_status'].value_counts().get('active')
    dissolved_companies = df['company_status'].value_counts().get('dissolved')
    liquidated_companies = df['company_status'].value_counts().get('liquidation')
    administration_companies = df['company_status'].value_counts().get('administration')
    recievership_companies = df['company_status'].value_counts().get('receivership')
    insolvent_companies = df['company_status'].value_counts().get('insolvency-proceedings')
    active_creation = df.loc[df['company_status'] == 'active']['year_of_creation'].value_counts()[0:3]
    if len(active_creation) < 3:
        active = len(active_creation)
    else:
        active = 3
    print(df["address"][0])
    print(str(active_companies) + " active companies")
    print(str(len(df)) + " companies registered")
    for i in range(active):
        print(str(active_creation[i]) + " active companies created in " + active_creation.keys()[i])
    # 3 most common periods of company survival in years
    print(str(dissolved_companies) + " dissolved companies")
    print(str(liquidated_companies) + " liquidated companies")
    print(str(administration_companies) + " companies in administration")
    print(str(recievership_companies) + " companies in recievership")
    print(str(insolvent_companies) + " companies in insolvency")
    survival = df['survival_years'].value_counts()
    if len(survival) > 0:
        if len(survival) < 3:
            survive = len(survival)
        else:
            survive = 3
        for i in range(survive):
            key = int(df['survival_years'].value_counts().keys()[i])
            print(str(df['survival_years'].value_counts()[key]) + " companies lasted " + str(int(key)) + "-" + str(int(key+1)) + " years")
            
def get_officers_at_location(location):
    url = "https://api.company-information.service.gov.uk/search/officers" + "?q=location:" + location
    time.sleep(0.5)
    response = requests.get(url, auth=basic)
    if response.status_code == 200:
        # filter json
        officers = []
        word_list = []
        for word in location.replace(',','').split(): 
            word_list.append(word)
        for officer in response.json()['items']:
            if all(word in officer['address_snippet'] for word in word_list):
                officers.append(officer)
        return officers

def get_officers(company_id):
    url = "https://api.company-information.service.gov.uk/company/" + company_id + "/officers"
    time.sleep(0.5)
    response = requests.get(url, auth=basic)
    if response.status_code == 200:
        return response.json()['items']
