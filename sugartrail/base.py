from sugartrail import api
from sugartrail import processing
import pandas as pd
import IPython
import numpy as np
import math
import warnings
from string import ascii_lowercase as alc
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 150)

class Network:
    def __init__(self, officer_id=None, company_id=None, address=None):
        self.addresses = pd.DataFrame(columns=['address','lat','lon','n','link_type','node_type','node'])
        self.officer_ids = pd.DataFrame(columns=['officer_id','name','n','link_type','node_type','node'])
        self.company_ids = pd.DataFrame(columns=['company_id','n','link_type','node_type','node',])
        self.companies = pd.DataFrame(columns=['company_number'])
        self.address_history = pd.DataFrame(columns=['company_number', 'address', 'start_date', 'end_date', 'lat', 'lon'])
        self._officer_id = officer_id
        self._company_id = company_id
        self._address = address
        self.n = 0
        self.link_type = None
        self.initialise_dataframe()
        self.hop = self.Hop()
        self.hop_history = pd.DataFrame()
        self.maxsize_entities = pd.DataFrame(columns=['node','type', 'maxsize_type', 'size'])

    @property
    def officer_id(self):
        return self._officer_id

    @officer_id.setter
    def officer_id(self, new_value):
        self._officer_id = new_value
        self._company_id = None
        self._address_id = None
        self.initialise_dataframe()

    @property
    def company_id(self):
        return self._company_id

    @company_id.setter
    def company_id(self, new_value):
        self._company_id = new_value
        self._officer_id = None
        self._address_id = None
        self.initialise_dataframe()

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, new_value):
        self._address = new_value
        self._company_id = None
        self._officer_id = None
        self.initialise_dataframe()

    def initialise_dataframe(self):
        self.company_ids = self.company_ids.iloc[0:0]
        self.officer_ids = self.officer_ids.iloc[0:0]
        self.addresses = self.addresses.iloc[0:0]
        if self._officer_id:
            if api.get_appointments(self._officer_id):
                self.officer_ids = self.officer_ids.append({'officer_id': self._officer_id, 'name': api.get_appointments(self._officer_id)['items'][0]['name'], 'n':self.n, 'link_type': None, 'node_type': None, 'node': None}, ignore_index=True)
        elif self.company_id:
            self.company_ids = self.company_ids.append({'company_id': self._company_id, 'n':self.n, 'link_type': None, 'node_type': None, 'node': None}, ignore_index=True)
            company = api.get_company(self._company_id)
            # company['n'] = self.n
            company['link_type'] = self.link_type
            self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)
        elif self._address:
            self.addresses = self.addresses.append({'address': self._address, 'n':self.n, 'link_type': None, 'node_type': None, 'node': None,}, ignore_index=True)
        else:
            print("No input provided. Please provide either officer_id, company_id or address value as input.")

    def add_company_names(self):
        self.company_ids['name'] = ''
        for i, row in self.company_ids.iterrows():
            self.company_ids['name'][i] = self.companies.loc[self.companies['company_number'] == self.company_ids['company_id'][i]]['company_name'].unique()[0]
        self.company_ids = self.company_ids[['company_id', 'name', 'n', 'link_type', 'node_type', 'node']]

    def get_company_from_id(self, company_df=None, company_id=None, print_progress=True):
        company_list = []
        if company_id:
            if company_id in self.company_ids['company_id'].unique():
                company_list = [company_id]
            else:
                print("add valid company id")
        else:
            company_list = self.company_ids['company_id'].unique()
        for i, company_id in enumerate(company_list):
            IPython.display.clear_output(wait=True)
            if print_progress:
                print("Processed " + str(i+1) + "/" + str(len(company_list)) + " companies.")
            if company_id not in self.companies['company_number'].unique():
                if company_df is not None:
                    try:
                        company = company_df[company_df[" CompanyNumber"] == str(company_id)]["CompanyName"].item()
                        if company:
                            self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)
                    except:
                        try:
                            company = api.get_company(company_id)
                            if company:
                                self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)
                        except:
                            print(f"Failed to get data for {company_id}")
                else:
                    company = api.get_company(company_id)
                    if company:
                        self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)

    def run_map_preprocessing(self):
        self.get_company_from_id()
        self.add_company_names()
        self.get_coords()
        return

    def get_coords(self):
        for i, row in self.addresses.iterrows():
            IPython.display.clear_output(wait=True)
            print("Processed " + str(i+1) + "/" + str(len(self.addresses)) + " addresses.")
            if row.isnull()['lat'] and row.isnull()['lon']:
                coords = processing.get_coords_from_address(row['address'])
                if coords:
                    self.addresses['lat'][i] = coords['lat']
                    self.addresses['lon'][i] = coords['lon']
                else:
                    print("No coords found: " + row['address'])
            historic_indices = self.address_history.index[self.address_history["address"]==row['address']].tolist()
            for j in historic_indices:
                self.address_history["lon"][j] = self.addresses['lon'][i]
                self.address_history["lat"][j] = self.addresses['lat'][i]

    def find_path(self, select_company):
        network_link_type_rows = self.company_ids.loc[self.company_ids['company_id'] == select_company]
        path = []
        company_info = self.get_company_from_id(company_id=select_company, print_progress=False)
        for i, row in network_link_type_rows.iterrows():
            path.insert(0, {'hop': row['n'], "type": "Company", "id": select_company, "node": self.companies[self.companies["company_number"] == select_company]['company_name'].item(), "node_type": row['link_type'], "link_id": row['node']})
            search_terms = [{'n': row['n']-1, 'node_type':row['node_type'], 'node':row['node']}]
            for j in range(row['n']-1,-1,-1):
                for term in search_terms:
                    if term['n'] == j:
                        if term['node_type'] == "Address":
                            select_rows = self.addresses.loc[(self.addresses['address'] == term['node']) & (self.addresses['n'] == j)]
                            for k, select_row in select_rows.iterrows():
                                if select_row['n'] == 0:
                                    origin = {'hop': j, "type": "Address", "id": select_row['address'], "node": select_row['address'], "node_type": "", "link_id": ""}
                                    if origin not in path:
                                        path.insert(0, origin)
                                        break
                                else:
                                    item = {'hop': j, "type": "Address", "id": select_row['address'], "node": select_row['address'], "node_type": select_row['link_type'], "link_id": select_row['node']}
                                    if item not in path:
                                        path.insert(0, item)
                                        search_terms.append({'n': j-1, 'node_type':select_row['node_type'], 'node':select_row['node']})
                        elif term['node_type'] == "Company":
                            select_rows = self.company_ids.loc[(self.company_ids['company_id'] == term['node']) & (self.company_ids['n'] == j)]
                            for l, select_row in select_rows.iterrows():
                                self.get_company_from_id(company_id=select_row['company_id'], print_progress=False)
                                if select_row['n'] == 0:
                                    origin = {'hop': j, "type": "Company", "id": select_row['company_id'], "node": self.companies[self.companies["company_number"] == select_row['company_id']]['company_name'].item(), "node_type": "", "link_id": ""}
                                    if origin not in path:
                                        path.insert(0, origin)
                                        break
                                else:
                                    item = {'hop': j, "type": "Company", "id": select_row['company_id'], "node": self.companies[self.companies["company_number"] == select_row['company_id']]['company_name'].item(), "node_type": select_row['link_type'], "link_id": select_row['node']}
                                    if item not in path:
                                        path.insert(0, item)
                                        search_terms.append({'n': j-1, 'node_type':select_row['node_type'], 'node':select_row['node']})
                        elif term['node_type'] == "Person":
                            select_rows = self.officer_ids.loc[(self.officer_ids['officer_id'] == term['node']) & (self.officer_ids['n'] == j)]
                            for m, select_row in select_rows.iterrows():
                                if select_row['link_type'] == 0:
                                    origin = {'hop': j, "type": "Person", "id": select_row["officer_id"], "node": select_row['name'], "node_type": "", "link_id": ""}
                                    if origin not in path:
                                        path.insert(0, origin)
                                        break
                                else:
                                    item = {'hop': j, "type": "Person", "id": select_row["officer_id"], "node": str(select_row['name']), "node_type": str(select_row['link_type']), "link_id": select_row['node']}
                                    if item not in path:
                                        path.insert(0, item)
                                        search_terms.append({'n': j-1, 'node_type':select_row['node_type'], 'node':select_row['node']})
                        else:
                            print(f"{row['node_type']} is invalid node_type")
                            break
        sorted_path = sorted(path, key=lambda d: d['hop'])
        for i in range(len(sorted_path)-1,-1,-1):
            search_term = sorted_path[i]['link_id']
            link_indices = []
            for j,item in enumerate(sorted_path):
                if item['id'] == search_term:
                    link_indices.append(alc[j].upper())
            sorted_path[i]["link"] = ','.join(link_indices)
            sorted_path[i]["node_index"] = alc[i].upper()
        return sorted_path

    def perform_hop(self, hops, company_data=None):
        for hop in range(hops):
            selected_addresses = self.addresses.loc[self.addresses['n'] == self.n]['address']
            selected_companies = self.company_ids.loc[self.company_ids['n'] == self.n]['company_id']
            selected_officers = self.officer_ids.loc[self.officer_ids['n'] == self.n]['officer_id']
            if len(selected_addresses.index) == 0 and len(selected_companies.index) == 0 and len(selected_officers.index) == 0:
                print("link_type of network reached.")
                break
            else:
                self.n += 1
                self.hop_history = self.hop_history.append(self.hop.__dict__, ignore_index=True)
                for i,address in enumerate(selected_addresses):
                    self.hop.search_address(self, address, company_data)
                    IPython.display.clear_output(wait=True)
                    print("Hop number: " + str(hop))
                    print("Processed " + str(i+1) + "/" + str(len(selected_addresses)) + " addresses.")
                for j,company in enumerate(selected_companies):
                    self.hop.search_company_id(self,company)
                    IPython.display.clear_output(wait=True)
                    print("Hop number: " + str(hop))
                    print("Processed " + str(len(selected_addresses)) + "/" + str(len(selected_addresses)) + " addresses.")
                    print("Processed " + str(j+1) + "/" + str(len(selected_companies)) + " companies.")
                for k,officer in enumerate(selected_officers):
                    self.hop.search_officer_id(self,officer)
                    IPython.display.clear_output(wait=True)
                    print("Hop number: " + str(hop))
                    print("Processed " + str(len(selected_addresses)) + "/" + str(len(selected_addresses)) + " addresses.")
                    print("Processed " + str(len(selected_companies)) + "/" + str(len(selected_companies)) + " companies.")
                    print("Processed " + str(k+1) + "/" + str(len(selected_officers)) + " officers.")

    class Hop:
        def __init__(self):
            self.get_company_officers = True
            self.get_company_address_history = True
            self.get_psc_correspondance_address = True
            self.get_officer_appointments = True
            self.officer_appointments_maxsize = 50
            self.get_officer_correspondance_address = True
            self.get_officer_duplicates = True
            self.officer_duplicates_maxsize = None
            self.get_officers_at_address = True
            self.officers_at_address_maxsize = 50
            self.get_companies_at_address = True
            self.companies_at_address_maxsize = 50

        def search_company_id(self, network, company_id):
            officers = []
            if self.get_company_officers:
                officers = api.get_company_officers(company_id)
                if officers:
                    officers = officers['items']
            network.node_type = "Company"
            network.node = company_id
            if officers:
                for officer in officers:
                    if processing.normalise_address(officer['address']) not in network.addresses[network.addresses['n'] < network.n]['address'].unique():
                        network.link_type = "Officer Corresponance Address"
                        network.addresses = network.addresses.append({'address': processing.normalise_address(officer['address']), 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
                    if officer['links']['officer']['appointments'].split('/')[2] not in network.officer_ids[network.officer_ids['n'] < network.n]['officer_id'].unique():
                        network.link_type = "Officer"
                        network.officer_ids = network.officer_ids.append({'officer_id': officer['links']['officer']['appointments'].split('/')[2], 'name': processing.normalise_name(officer['name']), 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
            if self.get_psc_correspondance_address:
                psc = api.get_psc(company_id)
                if psc:
                    for person in psc['items']:
                        if "address" in person:
                            network.link_type = "Person of Significant Control Address"
                            if processing.normalise_address(person['address']) not in network.addresses[network.addresses['n'] < network.n]['address'].unique():
                                network.addresses = network.addresses.append({'address': processing.normalise_address(person['address']), 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
            if self.get_company_address_history:
                address_history = processing.build_address_history(company_id)
                network.address_history = network.address_history.append(address_history, ignore_index=True)
                for address in address_history:
                    network.link_type = "Historic Address"
                    if address['address'] not in network.addresses[network.addresses['n'] < network.n]['address'].unique():
                        network.addresses = network.addresses.append({'address': address['address'], 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
            network.address_history = network.address_history.drop_duplicates().reset_index(drop=True)
            network.addresses = network.addresses.drop_duplicates().reset_index(drop=True)
            network.officer_ids = network.officer_ids.drop_duplicates().reset_index(drop=True)

        def search_officer_id(self, network, officer_id):
            network.node_type = "Person"
            network.node = officer_id
            appointments = api.get_appointments(officer_id)
            if appointments:
                if self.officer_appointments_maxsize == None or len(appointments['items']) < int(self.officer_appointments_maxsize or 0):
                    for appointment in appointments['items']:
                        if processing.normalise_address(appointment['address']) not in network.addresses[network.addresses['n'] < network.n]['address'].unique():
                            network.link_type = "Appointment Address"
                            network.addresses = network.addresses.append({'address': processing.normalise_address(appointment['address']), 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
                        if appointment['appointed_to']['company_number'] not in network.company_ids[network.company_ids['n'] < network.n]['company_id'].unique():
                            network.link_type = "Appointment"
                            network.company_ids = network.company_ids.append({'company_id': appointment['appointed_to']['company_number'], 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
                elif len(appointments['items']) > int(self.officer_appointments_maxsize):
                    network.maxsize_entities = network.maxsize_entities.append({'node':officer_id,'type': 'Officer', 'maxsize_type': 'Appointments', 'size': len(appointments['items'])}, ignore_index=True)
            if self.get_officer_correspondance_address:
                correspondance_address = api.get_correspondance_address(officer_id)
                if correspondance_address:
                    if processing.normalise_address(correspondance_address['items'][0]['address']) not in network.addresses[network.addresses['n'] < network.n]['address'].unique():
                        network.link_type = "Officer Corresponance Address"
                        network.addresses = network.addresses.append({'address': processing.normalise_address(correspondance_address['items'][0]['address']), 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
            if self.get_officer_duplicates:
                duplicate_officers = api.get_duplicate_officers(officer_id)
                if duplicate_officers:
                    if self.officer_duplicates_maxsize == None or len(duplicate_officers) < int(self.officer_duplicates_maxsize or 0):
                        for duplicate in duplicate_officers:
                            network.link_type = "Duplicate Officer"
                            if duplicate['links']['self'].split('/')[2] not in network.officer_ids[network.officer_ids['n'] < network.n]['officer_id'].unique():
                                network.officer_ids = network.officer_ids.append({'officer_id': duplicate['links']['self'].split('/')[2], 'name': duplicate['title'], 'n':network.n, 'link_type': network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
                    elif len(duplicate_officers) > int(self.officer_duplicates_maxsize):
                        network.maxsize_entities = network.maxsize_entities.append({'node':officer_id,'type': 'Officer', 'maxsize_type': 'Duplicates', 'size': len(duplicate_officers)}, ignore_index=True)
                network.addresses = network.addresses.drop_duplicates().reset_index(drop=True)
            network.officer_ids = network.officer_ids.drop_duplicates().reset_index(drop=True)
            network.company_ids = network.company_ids.drop_duplicates().reset_index(drop=True)

        def search_address(self, network, address, company_data):
            network.node_type = "Address"
            network.node = address
            if self.get_companies_at_address:
                # database method here:
                companies = {}
                if company_data is not None:
                    companies['items'] = processing.get_companies_from_address_database(address, company_data)
                else:
                    companies = api.get_companies_at_address(address)
                if companies:
                    if self.companies_at_address_maxsize == None or len(companies['items']) < int(self.companies_at_address_maxsize or 0):
                        company_ids = []
                        for company in companies['items']:
                            network.link_type = "Company at Address"
                            if company['company_number'] not in network.company_ids[network.company_ids['n'] < network.n]['company_id'].unique():
                                company_ids.append({'company_id': company['company_number'], 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node})
                        network.company_ids = network.company_ids.append(company_ids, ignore_index=True)
                    elif len(companies['items']) > int(self.companies_at_address_maxsize):
                        network.maxsize_entities = network.maxsize_entities.append({'node':address,'type': 'Address', 'maxsize_type': 'Companies', 'size': len(companies['items'])},ignore_index=True)

            if self.get_officers_at_address:
                officers = api.get_officers_at_address(address)
                if officers:
                    if self.officers_at_address_maxsize == None or len(officers) < int(self.officers_at_address_maxsize or 0):
                        for officer in officers:
                            network.link_type = "Officer at Address"
                            if officer['links']['self'].split('/')[2] not in network.officer_ids[network.officer_ids['n'] < network.n]['officer_id'].unique():
                                network.officer_ids = network.officer_ids.append({'officer_id': officer['links']['self'].split('/')[2], 'name': officer['title'], 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
                    elif len(officers) > int(self.officers_at_address_maxsize):
                        network.maxsize_entities = network.maxsize_entities.append({'node':address,'type': 'Address', 'maxsize_type': 'Officers', 'size': len(officers)},ignore_index=True)
            network.officer_ids = network.officer_ids.drop_duplicates().reset_index(drop=True)
            network.company_ids = network.company_ids.drop_duplicates().reset_index(drop=True)
