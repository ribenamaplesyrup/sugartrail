from sugartrail import api
from sugartrail import processing
import IPython
import numpy as np
import math
import warnings
import json
from string import ascii_letters as alc

class Network:
    def __init__(self, officer_id=None, company_id=None, address=None, file=None):
        self.addresses = []
        self.officer_ids = []
        self.company_ids = []
        self.companies = []
        self.address_history = []
        self._officer_id = officer_id
        self._company_id = company_id
        self._address = address
        self.n = 0
        self.link_type = None
        self.hop = self.Hop()
        self.hop_history = []
        self.maxsize_entities = []
        self.processed_officers  = []
        self.processed_companies = []
        self.processed_addresses = []
        self._file = self.load(file)
        self.initialise()

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, new_value):
        self._file = new_value
        self._officer_id = None
        self._company_id = None
        self._address_id = None
        self.load(self._file)

    @property
    def officer_id(self):
        return self._officer_id

    @officer_id.setter
    def officer_id(self, new_value):
        self._officer_id = new_value
        self._company_id = None
        self._address_id = None
        self.initialise()

    @property
    def company_id(self):
        return self._company_id

    @company_id.setter
    def company_id(self, new_value):
        self._company_id = new_value
        self._officer_id = None
        self._address_id = None
        self.initialise()

    @property
    def address(self, value):
        return self._address

    @address.setter
    def address(self, new_value):
        self._address = new_value
        self._company_id = None
        self._officer_id = None
        self.initialise()

    # change to initialise
    def initialise(self):
        if self.n < 1:
            if self._officer_id:
                if api.get_appointments(self._officer_id):
                    self.officer_ids.append(dict({'officer_id': self._officer_id, 'name': api.get_appointments(self._officer_id)['items'][0]['name'], 'n':self.n, 'link_type': None, 'node_type': None, 'node': None}))
                else:
                    print(f"Officer with ID:{str(self._officer_id)} not found")
            elif self._company_id:
                self.company_ids.append(dict({'company_id': self._company_id, 'n':self.n, 'link_type': '', 'node_type': '', 'node': ''}))
                company = api.get_company(self._company_id)
                self.companies.append(dict(processing.flatten(company)))
            elif self._address:
                self.addresses.append(dict({'address': self._address, 'n':self.n, 'link_type': '', 'node_type': '', 'node': ''}))
            elif self.file:
                pass
            else:
                print("No input provided. Please provide either officer_id, company_id or address value as input.")

    def save(self, filename, location='../assets/networks/'):
        network_data = {k: v for k, v in self.__dict__.items() if k != 'hop' and k != 'file'}
        saved_network = json.dumps(network_data)
        f = open(f'{filename}', 'w')
        f.write(saved_network)
        f.close

    def load(self, filename):
        if filename:
            f = open(f'../assets/networks/{filename}')
            network_data = json.load(f)
            self.addresses = network_data['addresses']
            self.officer_ids = network_data['officer_ids']
            self.company_ids = network_data['company_ids']
            self.companies = network_data['companies']
            self.address_history = network_data['address_history']
            self._officer_id = network_data['_officer_id']
            self._company_id = network_data['_company_id']
            self._address = network_data['_address']
            self.n = network_data['n']
            self.link_type = network_data['link_type']
            self.hop_history = network_data['hop_history']
            self.maxsize_entities = network_data['maxsize_entities']
            self.processed_officers  = network_data['processed_officers']
            self.processed_companies = network_data['processed_companies']
            self.processed_addresses = network_data['processed_addresses']

    def add_company_names(self):
        for i, row in enumerate(self.company_ids):
            company_details = list(filter(lambda d: d.get('company_number') == row['company_id'], self.companies))
            if company_details:
                self.company_ids[i]['company_name'] = company_details[0]['company_name']
            else:
                company_details = api.get_company(row['company_id'])
                if company_details:
                    if 'company_name' in  company_details:
                        self.company_ids[i]['company_name'] = company_details['company_name']

    def get_company_from_id(self, company_df=None, company_id=None, print_progress=True):
        company_list = []
        if company_id:
            if company_id in [company['company_id'] for company in self.company_ids]:
                company_list = [company_id]
            else:
                print("add valid company id")
        else:
            company_list = [company['company_id'] for company in self.company_ids]
        companies = []
        for i, company_id in enumerate(company_list):
            IPython.display.clear_output(wait=True)
            if print_progress:
                print("Processed " + str(i+1) + "/" + str(len(company_list)) + " companies.")
            if company_id not in [company['company_number'] for company in self.companies]:
                if company_df is not None:
                    try:
                        company = company_df[company_df[" CompanyNumber"] == str(company_id)]["CompanyName"].item()
                        if company:
                            # self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)
                            companies.append(company)
                    except:
                        try:
                            company = api.get_company(company_id)
                            if company:
                                # self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)
                                companies.append(company)
                        except:
                            print(f"Failed to get data for {company_id}")
                else:
                    company = api.get_company(company_id)
                    if company:
                        # self.companies = self.companies.append(pd.json_normalize(company), ignore_index=True)
                        companies.append(company)
        # add companies to dataframe
        self.companies.extend(companies)

    def run_map_preprocessing(self):
        # merge some of these methods:
        self.update_address_history()
        self.get_company_from_id()
        self.add_company_names()
        self.get_coords()
        self.address_history = [dict(t) for t in {tuple(d.items()) for d in self.address_history}]
        return

    def update_address_history(self):
        for i, company in enumerate(self.company_ids):
            IPython.display.clear_output(wait=True)
            print("Updated " + str(i+1) + "/" + str(len(self.company_ids)) + " company addresses.")
            if company['n'] == self.n:
                address_history = processing.build_address_history(company['company_id'])
                self.address_history.extend(address_history)

    def get_coords(self):
        for i, row in enumerate(self.addresses):
            IPython.display.clear_output(wait=True)
            print("Processed " + str(i+1) + "/" + str(len(self.addresses)) + " addresses.")
            if 'lat' not in row or 'lon' not in row:
                coords = processing.get_coords_from_address(row['address'])
                if coords:
                    self.addresses[i]['lat'] = coords['lat']
                    self.addresses[i]['lon'] = coords['lon']
                    historic_addresses = list(filter(lambda d: d.get('address') == row['address'], self.address_history))
                    for j, historic_address in enumerate(self.address_history):
                        if historic_address['address'] == row['address']:
                            self.address_history[j]['lon'] = coords['lon']
                            self.address_history[j]['lat'] = coords['lat']
                else:
                    self.addresses[i]['lat'] = ""
                    self.addresses[i]['lon'] = ""
                    print("No coords found: " + row['address'])

    def find_path(self, select_company):
        # network_link_type_rows = self.company_ids.loc[self.company_ids['company_id'] == select_company]
        network_link_type_rows = list(filter(lambda d: d.get('company_id') == select_company, self.company_ids))
        path = []
        company_info = self.get_company_from_id(company_id=select_company, print_progress=False)
        for i, row in enumerate(network_link_type_rows):
            path.insert(0, {'hop': row['n'], "type": "Company", "id": select_company, "node": row['company_name'], "node_type": row['link_type'], "link_id": row['node']})
            search_terms = [{'n': row['n']-1, 'node_type':row['node_type'], 'node':row['node']}]
            for j in range(row['n']-1,-1,-1):
                for term in search_terms:
                    if term['n'] == j:
                        if term['node_type'] == "Address":
                            ###
                            select_rows = list(filter(lambda d: d.get('address') == term['node'] and d.get('n') == j, self.addresses))
                            for k, select_row in enumerate(select_rows):
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
                            select_rows = list(filter(lambda d: d.get('company_id') == term['node'] and d.get('n') == j, self.company_ids))
                            for l, select_row in enumerate(select_rows):
                                self.get_company_from_id(company_id=select_row['company_id'], print_progress=False)
                                if select_row['n'] == 0:
                                    origin = {'hop': j, "type": "Company", "id": select_row['company_id'], "node": select_row['company_name'], "node_type": "", "link_id": ""}
                                    if origin not in path:
                                        path.insert(0, origin)
                                        break
                                else:
                                    item = {'hop': j, "type": "Company", "id": select_row['company_id'], "node": select_row['company_name'], "node_type": select_row['link_type'], "link_id": select_row['node']}
                                    if item not in path:
                                        path.insert(0, item)
                                        search_terms.append({'n': j-1, 'node_type':select_row['node_type'], 'node':select_row['node']})
                        elif term['node_type'] == "Person":
                            select_rows = list(filter(lambda d: d.get('officer_id') == term['node'] and d.get('n') == j, self.officer_ids))
                            for m, select_row in enumerate(select_rows):
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
                    link_indices.append(alc[j])
            sorted_path[i]["link"] = ','.join(link_indices)
            sorted_path[i]["node_index"] = alc[i]
        return sorted_path

    def perform_hop(self, hops, company_data=None):
        hop_history = []
        for hop in range(hops):
            # check if previous hop completed, if any processed items then its still mid-processing:
            selected_addresses = [address['address'] for address in list(filter(lambda d: d.get('n') == self.n, self.addresses))]
            selected_companies = [company['company_id'] for company in list(filter(lambda d: d.get('n') == self.n, self.company_ids))]
            selected_officers = [officer['officer_id'] for officer in list(filter(lambda d: d.get('n') == self.n, self.officer_ids))]
            if not selected_addresses and not selected_companies and not selected_officers:
                print("Edge of network reached.")
                break
            else:
                for i,address in enumerate(selected_addresses):
                    if address not in self.processed_addresses:
                        self.hop.search_address(self, address, company_data)
                        self.processed_addresses.append(address)
                    IPython.display.clear_output(wait=True)
                    print("Hop number: " + str(hop))
                    print("Processed " + str(i+1) + "/" + str(len(selected_addresses)) + " addresses.")
                for j,company in enumerate(selected_companies):
                    if company not in self.processed_companies:
                        self.hop.search_company_id(self,company)
                        self.processed_companies.append(company)
                    IPython.display.clear_output(wait=True)
                    print("Hop number: " + str(hop))
                    print("Processed " + str(len(selected_addresses)) + "/" + str(len(selected_addresses)) + " addresses.")
                    print("Processed " + str(j+1) + "/" + str(len(selected_companies)) + " companies.")
                for k,officer in enumerate(selected_officers):
                    if officer not in self.processed_officers:
                        self.hop.search_officer_id(self,officer)
                        self.processed_officers.append(officer)
                    IPython.display.clear_output(wait=True)
                    print("Hop number: " + str(hop))
                    print("Processed " + str(len(selected_addresses)) + "/" + str(len(selected_addresses)) + " addresses.")
                    print("Processed " + str(len(selected_companies)) + "/" + str(len(selected_companies)) + " companies.")
                    print("Processed " + str(k+1) + "/" + str(len(selected_officers)) + " officers.")
                self.officer_ids = [i for n, i in enumerate(self.officer_ids) if i not in self.officer_ids[n + 1:]]
                self.company_ids = [i for n, i in enumerate(self.company_ids) if i not in self.company_ids[n + 1:]]
                self.maxsize_entities = [i for n, i in enumerate(self.maxsize_entities) if i not in self.maxsize_entities[n + 1:]]
                self.addresses = [i for n, i in enumerate(self.addresses) if i not in self.addresses[n + 1:]]
                self.address_history = [i for n, i in enumerate(self.address_history) if i not in self.address_history[n + 1:]]
                self.companies = [i for n, i in enumerate(self.companies) if i not in self.companies[n + 1:]]
                self.processed_officers = []
                self.processed_companies = []
                self.processed_addresses = []
                self.n += 1
                hop_history.append(self.hop.__dict__)
            self.hop_history.extend(hop_history)

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
            new_addresses = []
            new_officers = []
            if self.get_company_officers:
                officers = api.get_company_officers(company_id)
                if officers:
                    officers = officers['items']
            network.node_type = "Company"
            network.node = company_id
            lower_n_addresses = [address['address'] for address in list(filter(lambda d: d.get('n') < network.n+1, network.addresses))]
            lower_n_officers = [officer['officer_id'] for officer in list(filter(lambda d: d.get('n') < network.n+1, network.officer_ids))]
            if officers:
                for officer in officers:
                    if 'address' in officer:
                        if processing.normalise_address(officer['address']) not in lower_n_addresses:
                            network.link_type = "Officer Corresponance Address"
                            new_address = {'address': processing.normalise_address(officer['address']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                            if new_address not in new_addresses:
                                new_addresses.append(new_address)
                            # network.addresses = network.addresses.append({'address': processing.normalise_address(officer['address']), 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
                        if officer['links']['officer']['appointments'].split('/')[2] not in lower_n_officers:
                            network.link_type = "Officer"
                            new_officer = {'officer_id': str(officer['links']['officer']['appointments'].split('/')[2]), 'name': processing.normalise_name(officer['name']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                            if new_officer not in new_officers:
                                new_officers.append(new_officer)
                            # network.officer_ids = network.officer_ids.append({'officer_id': officer['links']['officer']['appointments'].split('/')[2], 'name': processing.normalise_name(officer['name']), 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
            if self.get_psc_correspondance_address:
                psc = api.get_psc(company_id)
                if psc:
                    for person in psc['items']:
                        if "address" in person:
                            network.link_type = "Person of Significant Control Address"
                            if processing.normalise_address(person['address']) not in lower_n_addresses:
                                new_address = {'address': processing.normalise_address(person['address']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                                if new_address not in new_addresses:
                                    new_addresses.append(new_address)
            if self.get_company_address_history:
                address_history = processing.build_address_history(company_id)
                network.address_history.extend(address_history)
                for address in address_history:
                    network.link_type = "Historic Address"
                    if address['address'] not in lower_n_addresses:
                        new_address = {'address': address['address'], 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                        if new_address not in new_addresses:
                            new_addresses.append(dict({'address': address['address'], 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}))
                        # network.addresses = network.addresses.append({'address': address['address'], 'n':network.n, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}, ignore_index=True)
            network.addresses.extend(new_addresses)
            network.officer_ids.extend(new_officers)


        def search_officer_id(self, network, officer_id):
            new_addresses = []
            new_companies = []
            new_officers = []
            network.node_type = "Person"
            network.node = officer_id
            lower_n_addresses = [address['address'] for address in list(filter(lambda d: d.get('n') < network.n+1, network.addresses))]
            lower_n_officers = [officer['officer_id'] for officer in list(filter(lambda d: d.get('n') < network.n+1, network.officer_ids))]
            lower_n_companies = [company['company_id'] for company in list(filter(lambda d: d.get('n') < network.n+1, network.company_ids))]
            appointments = api.get_appointments(officer_id)
            if appointments:
                if self.officer_appointments_maxsize == None or len(appointments['items']) < int(self.officer_appointments_maxsize or 0):
                    for appointment in appointments['items']:
                        if processing.normalise_address(appointment['address']) not in lower_n_addresses:
                            network.link_type = "Appointment Address"
                            new_address = {'address': processing.normalise_address(appointment['address']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                            if new_address not in new_addresses:
                                new_addresses.append(new_address)
                        if appointment['appointed_to']['company_number'] not in lower_n_companies:
                            network.link_type = "Appointment"
                            new_company = {'company_id': appointment['appointed_to']['company_number'], 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                            if new_company not in new_companies:
                                new_companies.append(new_company)
                elif len(appointments['items']) > int(self.officer_appointments_maxsize):
                    network.maxsize_entities.append(dict({'node':officer_id,'type': 'Officer', 'maxsize_type': 'Appointments', 'size': len(appointments['items'])}))
            if self.get_officer_correspondance_address:
                correspondance_address = api.get_correspondance_address(officer_id)
                if correspondance_address:
                    if processing.normalise_address(correspondance_address['items'][0]['address']) not in lower_n_addresses:
                        network.link_type = "Officer Corresponance Address"
                        new_address = {'address': processing.normalise_address(correspondance_address['items'][0]['address']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                        if new_address not in new_addresses:
                            new_addresses.append(new_address)
            if self.get_officer_duplicates:
                duplicate_officers = api.get_duplicate_officers(officer_id)
                if duplicate_officers:
                    if self.officer_duplicates_maxsize == None or len(duplicate_officers) < int(self.officer_duplicates_maxsize or 0):
                        for duplicate in duplicate_officers:
                            network.link_type = "Duplicate Officer"
                            if duplicate['links']['self'].split('/')[2] not in lower_n_officers:
                                new_officer = {'officer_id': duplicate['links']['self'].split('/')[2], 'name': duplicate['title'], 'n':network.n+1, 'link_type': network.link_type, 'node_type': network.node_type, 'node': network.node}
                                if new_officer not in new_officers:
                                    new_officers.append(new_officer)
                    elif len(duplicate_officers) > int(self.officer_duplicates_maxsize):
                        network.maxsize_entities.append(dict({'node':officer_id,'type': 'Officer', 'maxsize_type': 'Duplicates', 'size': len(duplicate_officers)}))
            network.addresses.extend(new_addresses)
            network.officer_ids.extend(new_officers)
            network.company_ids.extend(new_companies)

        def search_address(self, network, address, company_data):
            new_companies = []
            new_officers = []
            network.node_type = "Address"
            network.node = address
            lower_n_addresses = [address['address'] for address in list(filter(lambda d: d.get('n') < network.n+1, network.addresses))]
            lower_n_officers = [officer['officer_id'] for officer in list(filter(lambda d: d.get('n') < network.n+1, network.officer_ids))]
            lower_n_companies = [company['company_id'] for company in list(filter(lambda d: d.get('n') < network.n+1, network.company_ids))]
            if self.get_companies_at_address:
                companies = {}
                if company_data is not None:
                    companies['items'] = processing.get_companies_from_address_database(address, company_data)
                else:
                    companies = api.get_companies_at_address(address)
                if companies:
                    if 'items' in companies:
                        if self.companies_at_address_maxsize == None or len(companies['items']) < int(self.companies_at_address_maxsize or 0):
                            for company in companies['items']:
                                network.link_type = "Company at Address"
                                if company['company_number'] not in lower_n_companies:
                                    new_company = {'company_id': company['company_number'], 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                                    if new_company not in new_companies:
                                        new_companies.append(new_company)
                        elif len(companies['items']) > int(self.companies_at_address_maxsize):
                            network.maxsize_entities.append(dict({'node':address,'type': 'Address', 'maxsize_type': 'Companies', 'size': len(companies['items'])}))
            if self.get_officers_at_address:
                officers = api.get_officers_at_address(address)
                if officers:
                    if self.officers_at_address_maxsize == None or len(officers) < int(self.officers_at_address_maxsize or 0):
                        for officer in officers:
                            if 'links' and 'title' in officer:
                                network.link_type = "Officer at Address"
                                if officer['links']['self'].split('/')[2] not in lower_n_officers:
                                    new_officer = {'officer_id': officer['links']['self'].split('/')[2], 'name': officer['title'], 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                                    if new_officer not in new_officers:
                                        new_officers.append(new_officer)
                    elif len(officers) > int(self.officers_at_address_maxsize):
                        network.maxsize_entities.append(dict({'node':address,'type': 'Address', 'maxsize_type': 'Officers', 'size': len(officers)}))
            network.officer_ids.extend(new_officers)
            network.company_ids.extend(new_companies)
