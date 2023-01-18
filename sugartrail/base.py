import sugartrail
import IPython
import json
import functools
from string import ascii_letters as alc

class Network:
    """Class represents a network of connected companies, officers and
    addresses. Class contains methods to build network of user defined size from
    a single seed company, officer or address."""
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
        self.initialise_node(officer_id, company_id, address, file)

    def clear_state(func):
        """Resets the class attributes to pre-init state."""
        @functools.wraps(func)
        def wrapper_clear(*args, **kwargs):
            args[0].addresses = []
            args[0].officer_ids = []
            args[0].company_ids = []
            args[0].companies = []
            args[0].address_history = []
            args[0]._officer_id = None
            args[0]._company_id = None
            args[0]._address = None
            args[0].n = 0
            args[0].link_type = None
            args[0].hop_history = []
            args[0].maxsize_entities = []
            args[0].processed_officers  = []
            args[0].processed_companies = []
            args[0].processed_addresses = []
            func(*args, **kwargs)
        return wrapper_clear

    @property
    def officer_id(self):
        """officer_id property representing seed officer."""
        return self._officer_id

    @officer_id.setter
    @sugartrail.api.auth
    def officer_id(self, new_value):
        """officer_id setter that checks if officer_id exists in Companies House before setting value."""
        officer_info = sugartrail.api.get_appointments(new_value)
        if officer_info:
            self._officer_id = new_value
            self.officer_ids = [{
                'officer_id': new_value,
                'name': officer_info['items'][0]['name'],
                'n':self.n,
                'link_type': None,
                'node_type': None,
                'node': None}]
        else:
            print(f"Officer with ID:{str(new_value)} not found")
            self._officer_id = None

    @property
    def company_id(self):
        """company_id property representing seed company."""
        return self._company_id

    @company_id.setter
    @sugartrail.api.auth
    def company_id(self, new_value):
        """company_id setter that checks if company_id exists in Companies House before setting value."""
        company_info = sugartrail.api.get_company(new_value)
        if company_info:
            self._company_id = new_value
            self.company_ids = [{
                'company_id': self._company_id,
                'n':self.n,
                'link_type': '',
                'node_type': '',
                'node': ''}]
            self.companies = [dict(sugartrail.processing.flatten(company_info))]
        else:
            print(f"Company with ID:{str(new_value)} not found")
            self._company_id = None

    @property
    def address(self, value):
        """address property representing seed address."""
        return self._address

    @address.setter
    @sugartrail.api.auth
    def address(self, new_value):
        """address setter."""
        self._address = new_value
        self.addresses = [dict({'address': self._address,
         'n':self.n,
         'link_type': '',
         'node_type': '',
         'node': ''})]

    @property
    def file(self):
        """file property for loading pre-built network data into class."""
        return self._file

    @file.setter
    def file(self, new_value):
        """file setter for loading pre-built network data into class."""
        self._file = new_value
        self.load(self._file)

    @clear_state
    def initialise_node(self, officer_id, company_id, address ,file):
        """Builds initial network from arguments."""
        if self.n < 1:
            if officer_id:
                self.officer_id = officer_id
            elif company_id:
                self.company_id = company_id
            elif address:
                self.address = address
            elif file:
                self.file = file
            else:
                print("No input provided. Please provide either officer_id, company_id, address or file as input.")

    def save(self, filename, location='../assets/networks/'):
        """Saves network in JSON format to '../assets/networks/'."""
        network_data = {k: v for k, v in self.__dict__.items() if k != 'hop' and k != 'file'}
        saved_network = json.dumps(network_data)
        f = open(location + f'{filename}', 'w')
        f.write(saved_network)
        f.close

    def load(self, filename):
        """Loads network stored in JSON format from '../assets/networks/'."""
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

    def run_map_preprocessing(self):
        """Gets missing/additional information on companies and addresses required for
        mapping them. This includes address histories, company records and coordinates."""
        self.get_address_histories()
        self.get_company_records_from_id()
        self.get_coords()
        return

    def get_address_histories(self):
        """Gets missing address histories for companies at the edge of the network."""
        historic_address_company_ids = list(dict.fromkeys([company['company_number'] for company in self.address_history]))
        for i, company in enumerate(self.company_ids):
            IPython.display.clear_output(wait=True)
            print("Updated " + str(i+1) + "/" + str(len(self.company_ids)) + " company addresses.")
            # if company is at the edge of the network:
            # if historic address not in
            if company['company_id'] not in historic_address_company_ids:
                historic_address_company_ids.append(company['company_id'])
                address_history = sugartrail.processing.build_address_history(company['company_id'])
                historic_addresses = []
                for historic_address in address_history:
                    if historic_address not in self.address_history:
                        historic_addresses.append(historic_address)
                self.address_history.extend(historic_addresses)

    def get_company_records_from_id(self, company_df=None, print_progress=True):
        """Gets company records for all company IDs in the network. Additionally
        enriches company_ids with company names for improved readability."""
        company_list = [company['company_id'] for company in self.company_ids]
        companies = []
        for i, company_id in enumerate(company_list):
            IPython.display.clear_output(wait=True)
            if print_progress:
                print("Processed " + str(i+1) + "/" + str(len(company_list)) + " companies.")
            if company_id not in [company['company_number'] for company in self.companies]:
                # if using local Companies House data
                if company_df is not None:
                    try:
                        company = company_df[company_df[" CompanyNumber"] == str(company_id)]["CompanyName"].item()
                        if company:
                            companies.append(company)
                    except:
                        try:
                            company = sugartrail.api.get_company(company_id)
                            if company:
                                companies.append(company)
                        except:
                            print(f"Failed to get data for {company_id}")
                # otherwise uses API
                else:
                    company = sugartrail.api.get_company(company_id)
                    if company:
                        companies.append(company)
                        # update company_ids with company name
                        self.company_ids[i]['company_name'] = company['company_name']
            else:
                self.company_ids[i]['company_name'] = list(filter(lambda d: d.get('company_number') == company_id, self.companies))[0]['company_name']
        self.companies.extend(companies)

    def get_coords(self):
        """Gets coordinates for each address in addresses and address_history."""
        for i, row in enumerate(self.addresses):
            IPython.display.clear_output(wait=True)
            print("Processed " + str(i+1) + "/" + str(len(self.addresses)) + " addresses.")
            if 'lat' not in row or 'lon' not in row:
                coords = sugartrail.processing.get_coords_from_address(row['address'])
                if coords:
                    self.addresses[i]['lat'] = coords['lat']
                    self.addresses[i]['lon'] = coords['lon']
                    historic_addresses = list(filter(lambda d: d.get('address') == row['address'], self.address_history))
                    for j, historic_address in enumerate(self.address_history):
                        if historic_address['address'] == row['address']:
                            self.address_history[j]['lon'] = coords['lon']
                            self.address_history[j]['lat'] = coords['lat']
                else:
                    # no coords found
                    self.addresses[i]['lat'] = ""
                    self.addresses[i]['lon'] = ""

    def find_path(self, select_company):
        """Finds path from 'select_company' to origin company'."""
        # retrieve rows containing selected company:
        network_link_type_rows = list(filter(lambda d: d.get('company_id') == select_company, self.company_ids))
        path = []
        # iterate through each path from selected company to seed company:
        for i, row in enumerate(network_link_type_rows):
            # insert end of path node:
            path.insert(0, {'hop': row['n'], "type": "Company", "id": select_company, "node": row['company_name'], "node_type": row['link_type'], "link_id": row['node']})
            # define search terms for locating connected nodes:
            search_terms = [{'n': row['n']-1, 'node_type':row['node_type'], 'node':row['node']}]
            # iterate through degrees of seperation till origin is reached:
            for j in range(row['n']-1,-1,-1):
                for term in search_terms:
                    if term['n'] == j:
                        if term['node_type'] == "Address":
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
        # add letter correspondance for readability
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
        """Gets companies, officers and addresses within n-degrees of seperation
        from current nodes, where n is the number of hops."""
        hop_history = []
        for hop in range(hops):
            # select the nodes for which the method will retrieve other nodes
            # 1-degree of seperation from:
            selected_addresses = [address['address'] for address in list(filter(lambda d: d.get('n') == self.n, self.addresses))]
            selected_companies = [company['company_id'] for company in list(filter(lambda d: d.get('n') == self.n, self.company_ids))]
            selected_officers = [officer['officer_id'] for officer in list(filter(lambda d: d.get('n') == self.n, self.officer_ids))]
            if not selected_addresses and not selected_companies and not selected_officers:
                print("Edge of network reached.")
                break
            else:
                for i,address in enumerate(selected_addresses):
                    # in-case method was run previously and failed to complete,
                    # check if address was previously processed:
                    if address not in self.processed_addresses:
                        self.hop.search_address(self, address, company_data)
                        self.processed_addresses.append(address)
                    IPython.display.clear_output(wait=True)
                    print("Hop number: " + str(hop+1))
                    print("Processed " + str(i+1) + "/" + str(len(selected_addresses)) + " addresses.")
                for j,company in enumerate(selected_companies):
                    # in-case method was run previously and failed to complete,
                    # check if company was previously processed:
                    if company not in self.processed_companies:
                        self.hop.search_company_id(self,company)
                        self.processed_companies.append(company)
                    IPython.display.clear_output(wait=True)
                    print("Hop number: " + str(hop+1))
                    print("Processed " + str(len(selected_addresses)) + "/" + str(len(selected_addresses)) + " addresses.")
                    print("Processed " + str(j+1) + "/" + str(len(selected_companies)) + " companies.")
                for k,officer in enumerate(selected_officers):
                    # in-case method was run previously and failed to complete,
                    # check if officer was previously processed:
                    if officer not in self.processed_officers:
                        self.hop.search_officer_id(self,officer)
                        self.processed_officers.append(officer)
                    IPython.display.clear_output(wait=True)
                    print("Hop number: " + str(hop+1))
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
        """Class attributes store the criteria for each hop. Class contains
        methods for getting officers, addresses and companies using the
        criteria."""
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
            """Gets officers and addresses connected to input company
            (company_id)."""
            officers = []
            new_addresses = []
            new_officers = []
            if self.get_company_officers:
            # get officers at company
                officers = sugartrail.api.get_company_officers(company_id)
                if officers:
                    if 'items' in officers:
                        officers = officers['items']
            # process officer results
            network.node_type = "Company"
            network.node = company_id
            # find addresses and officers already added to the network
            lower_n_addresses = [address['address'] for address in list(filter(lambda d: d.get('n') < network.n+1, network.addresses))]
            lower_n_officers = [officer['officer_id'] for officer in list(filter(lambda d: d.get('n') < network.n+1, network.officer_ids))]
            if officers:
                for officer in officers:
                    # if 'address' in officer:
                    #     # check address not already in the network
                    #     if sugartrail.processing.normalise_address(officer['address']) not in lower_n_addresses:
                    #         network.link_type = "Officer Corresponance Address"
                    #         new_address = {'address': sugartrail.processing.normalise_address(officer['address']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                    #         if new_address not in new_addresses:
                    #             new_addresses.append(new_address)
                    #     # check not already in the network
                    if officer['links']['officer']['appointments'].split('/')[2] not in lower_n_officers:
                        network.link_type = "Officer"
                        new_officer = {'officer_id': str(officer['links']['officer']['appointments'].split('/')[2]), 'name': sugartrail.processing.normalise_name(officer['name']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                        if new_officer not in new_officers:
                            new_officers.append(new_officer)
            if self.get_psc_correspondance_address:
            # get address for company pscs
                psc = sugartrail.api.get_psc(company_id)
                if psc:
                    if 'items' in psc:
                        for person in psc['items']:
                            if "address" in person:
                                network.link_type = "Person of Significant Control Address"
                                if sugartrail.processing.normalise_address(person['address']) not in lower_n_addresses:
                                    new_address = {'address': sugartrail.processing.normalise_address(person['address']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                                    if new_address not in new_addresses:
                                        new_addresses.append(new_address)
            if self.get_company_address_history:
            # get company address history
                address_history = sugartrail.processing.build_address_history(company_id)
                network.address_history.extend(address_history)
                for address in address_history:
                    network.link_type = "Historic Address"
                    if 'address' in address:
                        if address['address'] not in lower_n_addresses:
                            new_address = {'address': address['address'], 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                            if new_address not in new_addresses:
                                new_addresses.append(dict({'address': address['address'], 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}))
            network.addresses.extend(new_addresses)
            network.officer_ids.extend(new_officers)


        def search_officer_id(self, network, officer_id):
            """Gets officers, companies and addresses connected to input officer
            (officer_id)."""
            new_addresses = []
            new_companies = []
            new_officers = []
            network.node_type = "Person"
            network.node = officer_id
            lower_n_addresses = [address['address'] for address in list(filter(lambda d: d.get('n') < network.n+1, network.addresses))]
            lower_n_officers = [officer['officer_id'] for officer in list(filter(lambda d: d.get('n') < network.n+1, network.officer_ids))]
            lower_n_companies = [company['company_id'] for company in list(filter(lambda d: d.get('n') < network.n+1, network.company_ids))]
            appointments = sugartrail.api.get_appointments(officer_id)
            if appointments:
                if self.officer_appointments_maxsize == None or len(appointments['items']) < int(self.officer_appointments_maxsize or 0):
                    for appointment in appointments['items']:
                        if sugartrail.processing.normalise_address(appointment['address']) not in lower_n_addresses:
                            network.link_type = "Appointment Address"
                            new_address = {'address': sugartrail.processing.normalise_address(appointment['address']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
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
                correspondance_address = sugartrail.api.get_correspondance_address(officer_id)
                if correspondance_address:
                    if sugartrail.processing.normalise_address(correspondance_address['items'][0]['address']) not in lower_n_addresses:
                        network.link_type = "Officer Corresponance Address"
                        new_address = {'address': sugartrail.processing.normalise_address(correspondance_address['items'][0]['address']), 'n':network.n+1, 'link_type':network.link_type, 'node_type': network.node_type, 'node': network.node}
                        if new_address not in new_addresses:
                            new_addresses.append(new_address)
            if self.get_officer_duplicates:
                duplicate_officers = sugartrail.api.get_duplicate_officers(officer_id)
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
            """Gets officers, companies and addresses connected to input officer
            (officer_id)."""
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
                    companies['items'] = sugartrail.processing.get_companies_from_address_database(address, company_data)
                else:
                    companies = sugartrail.api.get_companies_at_address(address)
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
                officers = sugartrail.api.get_officers_at_address(address)
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
