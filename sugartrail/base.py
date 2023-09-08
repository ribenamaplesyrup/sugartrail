import sugartrail
import IPython
import json
import functools
import pandas as pd

class Network:
    """Class represents a network of connected companies, officers and
    addresses. Class contains methods to build network of user defined size from
    a single seed company, officer or address."""
    def __init__(self, officer_id=None, company_id=None, address=None, file=None):
        self.graph = {}
        self.company_records = []
        self.address_history = []
        self._officer_id = officer_id
        self._company_id = company_id
        self._address = address
        self.n = 0
        self.hop = sugartrail.hop.Hop()
        self.hop_history = []
        self.maxsize_entities = []
        self.progress = sugartrail.progress.Progress()
        self._file = self.load(file)
        self.initialise_node(officer_id, company_id, address, file)

    def clear_state(func):
        """Resets the class attributes to pre-init state."""
        @functools.wraps(func)
        def wrapper_clear(*args, **kwargs):
            args[0].graph = {}
            args[0].company_records = []
            args[0].address_history = []
            args[0]._officer_id = None
            args[0]._company_id = None
            args[0]._address = None
            args[0].n = 0
            args[0].link_type = None
            args[0].hop_history = []
            args[0].maxsize_entities = []
            # args[0].processed_officers  = []
            # args[0].processed_companies = []
            # args[0].processed_addresses = []
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
            self.graph = {
                new_value: {
                    'title': officer_info['items'][0]['name'],
                    'depth':self.n,
                    'node_type': "Person",
                    'arcs': []
                    }
                }
        else:
            print(f"Officer with ID:{str(new_value)} not found")
            self._officer_id = None

    @property
    def officer_ids(self):
        """Get all officers from graph."""
        officer_ids = {k: v for k, v in self.graph.items() if v['node_type'] == 'Person'}
        officer_table = []
        for officer_id, officer_data in officer_ids.items():
            officer = {
                    "officer_id": officer_id,
                    "title": officer_data['title'],
                    "depth": officer_data['depth'],
                    "title": officer_data['title'],
                    'link_type': '',
                    'link': ''
                }
            if not officer_data['arcs']:
                officer_table.append(officer)
            else:
                for arc in officer_data['arcs']:
                    officer.update({
                        'link_type': arc['arc_type'],
                        'link': arc['start_node']
                    })
                    officer_table.append(officer)
        return officer_table

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
            self.graph = {
                new_value: {
                    'title': company_info['company_name'],
                    'depth':self.n,
                    'node_type': "Company",
                    'arcs': []
                    }
                }
            # self.companies = [dict(sugartrail.processing.flatten(company_info))]
        else:
            print(f"Company with ID:{str(new_value)} not found")
            self._company_id = None

    @property
    def company_ids(self):
        company_ids = {k: v for k, v in self.graph.items() if v['node_type'] == 'Company'}
        company_table = []
        for company_id, company_data in company_ids.items():
            company = {
                    "company_id": company_id,
                    "title": company_data['title'],
                    "depth": company_data['depth'],
                    "title": company_data['title'],
                    'link_type': '',
                    'link': ''
                }
            if not company_data['arcs']:
                company_table.append(company)
            else:
                for arc in company_data['arcs']:
                    company.update({
                        'link_type': arc['arc_type'],
                        'link': arc['start_node']
                    })
                    company_table.append(company)
        return company_table

    @property
    def address(self, value):
        """address property representing seed address."""
        return self._address

    @address.setter
    @sugartrail.api.auth
    def address(self, new_value):
        """address setter."""
        self._address = new_value
        self.graph = {
            new_value: {
                'title': new_value,
                'depth':self.n,
                'node_type': "Address",
                'arcs': []
                }
            }

    @property
    def addresses(self):
        addresses = {k: v for k, v in self.graph.items() if v['node_type'] == 'Address'}
        address_table = []
        for address_string, address_data in addresses.items():
            address = {
                    "address": address_string,
                    "title": address_data['title'],
                    "depth": address_data['depth'],
                    "title": address_data['title'],
                    'link_type': '',
                    'link': ''
                }
            if not address_data['arcs']:
                address_table.append(address)
            else:
                for arc in address_data['arcs']:
                    address.update({
                        'link_type': arc['arc_type'],
                        'link': arc['start_node']
                    })
                    address_table.append(address)
        return address_table

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
        network_data = {k: v for k, v in self.__dict__.items() if k not in ['hop', 'file', 'progress']}
        saved_network = json.dumps(network_data)
        f = open(location + f'{filename}', 'w')
        f.write(saved_network)
        f.close

    def load(self, filename):
        """Loads network stored in JSON format."""
        if filename:
            f = open(f'{filename}')
            network_data = json.load(f)
            self.graph = network_data['graph']
            self.company_records = network_data['company_records']
            self.address_history = network_data['address_history']
            self._officer_id = network_data['_officer_id']
            self._company_id = network_data['_company_id']
            self._address = network_data['_address']
            self.n = network_data['n']
            self.link_type = network_data['link_type']
            self.hop_history = network_data['hop_history']
            self.maxsize_entities = network_data['maxsize_entities']
            # self.processed_officers  = network_data['processed_officers']
            # self.processed_companies = network_data['processed_companies']
            # self.processed_addresses = network_data['processed_addresses']

    def run_map_preprocessing(self):
        """Gets missing/additional information on companies and addresses required for
        mapping them. This includes address histories, company records and coordinates."""
        self.get_network_edge_address_histories()
        self.get_company_records_from_id()
        self.get_coords()
        return

    def get_company_records_from_id(self, company_df=None, print_progress=True):
        """Gets company records for all company IDs in the network."""
        company_list = [item for item in self.graph.keys() if self.graph[item]['node_type'] == 'Company']
        company_records = []
        for i, company_id in enumerate(company_list):
            IPython.display.clear_output(wait=True)
            if print_progress:
                print("Processed " + str(i+1) + "/" + str(len(company_list)) + " companies.")
            if company_id not in [company['company_number'] for company in self.company_records]:
                if company_df is not None:
                    try:
                        company = company_df[company_df[" CompanyNumber"] == str(company_id)]["CompanyName"].item()
                        if company:
                            company_records.append(company)
                    except:
                        try:
                            company = sugartrail.api.get_company(company_id)
                            if company:
                                company_records.append(company)
                        except:
                            print(f"Failed to get data for {company_id}")
                else:
                    company = sugartrail.api.get_company(company_id)
                    if company:
                        company_records.append(company)
        self.company_records.extend(company_records)

    def get_network_edge_address_histories(self):
        """Gets missing address histories for companies at the edge of the network."""
        if self.hop.get_company_address_history:
            network_edge_companies = []
            for item in self.graph.keys():
                if self.graph[item]['depth'] == self.n and self.graph[item]['node_type'] == 'Company':
                    network_edge_companies.append(item)
            for i, company in enumerate(network_edge_companies):
                IPython.display.clear_output(wait=True)
                print("Processed " + str(i+1) + "/" + str(len(network_edge_companies)) + " company addresses.")
                # get company address history
                address_history = sugartrail.processing.build_address_history(company)
                if address_history:
                    # self.address_history.extend(address_history)
                    for address in address_history:
                        if 'address' in address:
                            self.address_history.append(address)
                            new_address = address['address']
                            if new_address not in self.graph:
                                self.graph[new_address] = {
                                    'depth': self.n+1,
                                    'title': new_address,
                                    'node_type': "Address",
                                    'arcs': []
                                    }
                            arc = {
                                'arc_type': "Historic Address",
                                'start_node': company
                            }
                            if arc not in self.graph[new_address]['arcs'] and self.graph[new_address]['depth'] == self.n+1:
                                self.graph[new_address]['arcs'].append(arc)

    def get_coords(self):
        """Gets coordinates for each address in addresses and address_history."""
        address_coords = {}
        for i, address in enumerate(self.address_history):
            IPython.display.clear_output(wait=True)
            print("Processed " + str(i+1) + "/" + str(len(self.address_history)) + " addresses.")
            if address['address'] not in address_coords:
                coords = sugartrail.processing.get_coords_from_address(address['address'])
                if coords:
                    address_coords[address['address']] = {'lat': coords['lat'], 'lon': coords['lon']}
                else:
                    address_coords[address['address']] = {'lat': '', 'lon': ''}
            self.address_history[i]['lat'] = address_coords[address['address']]['lat']
            self.address_history[i]['lon'] = address_coords[address['address']]['lon']
            self.graph[address['address']]['lat'] = address_coords[address['address']]['lat']
            self.graph[address['address']]['lon'] = address_coords[address['address']]['lon']

    def find_path(self, company_id):
        """Finds path from 'select_company' to origin company'."""
        path = []
        end_node = dict(self.graph[company_id])
        if not end_node['arcs']:
            # start_node selected
            end_node.update({
                'id': company_id,
                'link_type': '',
                'link': ''
                })
            path.append(dict((k, end_node[k]) for k in ('title', 'depth', 'node_type', 'id', 'link', 'link_type')))
        else:
            # work back from the end node to the start node
            for arc in end_node['arcs']:
                connection = dict((k, end_node[k]) for k in ('title', 'depth', 'node_type'))
                connection.update({
                    'id': company_id,
                    'link_type': arc['arc_type'],
                    'link': arc['start_node']
                    })
                path.append(connection)
            for connection in path:
                id = connection['link']
                node = dict(self.graph[id])
                if node['arcs']:
                    for arc in node['arcs']:
                        connection = dict((k, node[k]) for k in ('title', 'depth', 'node_type'))
                        connection.update({
                            'id': id,
                            'link_type': arc['arc_type'],
                            'link': arc['start_node']
                            })
                        if connection not in path:
                            path.append(connection)
                else:
                    start_node = dict((k, node[k]) for k in ('title', 'depth', 'node_type'))
                    start_node.update({
                        'id': id,
                        'link_type': '',
                        'link': ''
                        })
                    path.append(start_node)
                    break
        path.reverse()
        path = sugartrail.processing.condense_path(path)
        path = sugartrail.processing.asciiify_path(path)
        return path

    def perform_hop(self, hops, company_data=None, print_progress=True):
        """Gets companies, officers and addresses within n-degrees of seperation
        from current nodes, where n is the number of hops."""
        hop_history = []
        for hop in range(hops):
            self.progress.intro_print = "Hop number: " + str(hop+1)
            # retrieve addresses, companies and officers at edge of network
            for k in self.graph.keys():
                if self.graph[k]['depth'] == self.n:
                    if self.graph[k]['node_type'] == 'Address':
                        self.progress.selected_addresses.append(k)
                    elif self.graph[k]['node_type'] == 'Person':
                        self.progress.selected_officers.append(k)
                    elif self.graph[k]['node_type'] == 'Company':
                        self.progress.selected_companies.append(k)
            if not self.progress.selected_addresses and not self.progress.selected_companies and not self.progress.selected_officers:
                print("Edge of network reached.")
                break
            else:
                for i,address in enumerate(self.progress.selected_addresses):
                    self.progress.address_index = i
                    if address not in self.progress.processed_addresses:
                        self.hop.search_address(self, address, company_data)
                        self.progress.processed_addresses.append(address)
                    if print_progress:
                        self.progress.print_progress()
                for j,company in enumerate(self.progress.selected_companies):
                    self.progress.company_index = j
                    if company not in self.progress.processed_companies:
                        self.hop.search_company_id(self,company)
                        self.progress.processed_companies.append(company)
                    if print_progress:
                        self.progress.print_progress()
                for k,officer in enumerate(self.progress.selected_officers):
                    self.progress.officer_index = k
                    if officer not in self.progress.processed_officers:
                        self.hop.search_officer_id(self,officer)
                        self.progress.processed_officers.append(officer)
                    if print_progress:
                        self.progress.print_progress()
                self.maxsize_entities = [i for n, i in enumerate(self.maxsize_entities) if i not in self.maxsize_entities[n + 1:]]
                self.progress.processed_officers, self.progress.processed_companies,  self.progress.processed_addresses = [],[],[]
                self.progress.selected_officers, self.progress.selected_companies,  self.progress.selected_addresses = [],[],[]
                self.n += 1
                hop_history.append(self.hop.__dict__)
            self.hop_history.extend(hop_history)
