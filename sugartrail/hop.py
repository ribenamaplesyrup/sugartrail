import sugartrail

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
        if self.get_company_officers:
            officers = sugartrail.api.get_company_officers(company_id)
            if officers:
                if 'items' in officers:
                    officers = officers['items']
        if officers:
            for officer in officers:
                new_officer_id = str(officer['links']['officer']['appointments'].split('/')[2])
                if new_officer_id not in network.graph:
                    try:
                        title = sugartrail.api.get_appointments(new_officer_id)['items'][0]['name']
                    except:
                        print(f"failed to get title for officer: {new_officer_id}")
                        try:
                            title = sugartrail.processing.normalise_name(officer['name'])
                        except:
                            print(f"failed to get title for officer: {new_officer_id}") 
                            title = new_officer_id
                    network.graph[new_officer_id] = {
                        'depth': network.n+1,
                        'title': title,
                        'node_type': "Person",
                        'arcs': []
                    }
                arc = {
                    'arc_type': "Officer",
                    'start_node': company_id
                }
                if arc not in network.graph[new_officer_id]['arcs'] and network.graph[new_officer_id]['depth'] == network.n+1:
                    network.graph[new_officer_id]['arcs'].append(arc)
        if self.get_psc_correspondance_address:
        # get address for company pscs
            psc = sugartrail.api.get_psc(company_id)
            if psc:
                if 'items' in psc:
                    for person in psc['items']:
                        if "address" in person:
                            new_address = sugartrail.processing.normalise_address(person['address'])
                            if new_address not in network.graph:
                                network.graph[new_address] = {
                                    'depth': network.n+1,
                                    'title': new_address,
                                    'node_type': "Address",
                                    'arcs': []
                                }
                            arc = {
                                'arc_type': "Person of Significant Control Address",
                                'start_node': company_id
                            }
                            if arc not in network.graph[new_address]['arcs'] and network.graph[new_address]['depth'] == network.n+1:
                                network.graph[new_address]['arcs'].append(arc)
        if self.get_company_address_history:
        # get company address history
            address_history = sugartrail.processing.build_address_history(company_id)
            # network.address_history.extend(address_history)
            if address_history:
                for address in address_history:
                    if 'address' in address:
                        network.address_history.append(address)
                        new_address = address['address']
                        if new_address not in network.graph:
                            network.graph[new_address] = {
                                'depth': network.n+1,
                                'title': new_address,
                                'node_type': "Address",
                                'arcs': []
                            }
                        arc = {
                            'arc_type': "Historic Address",
                            'start_node': company_id
                        }
                        if arc not in network.graph[new_address]['arcs'] and network.graph[new_address]['depth'] == network.n+1:
                            network.graph[new_address]['arcs'].append(arc)

    def search_officer_id(self, network, officer_id):
        """Gets officers, companies and addresses connected to input officer
        (officer_id)."""
        appointments = sugartrail.api.get_appointments(officer_id)
        if appointments:
            if self.officer_appointments_maxsize == None or len(appointments['items']) < int(self.officer_appointments_maxsize or 0):
                for appointment in appointments['items']:
                    new_company = appointment['appointed_to']['company_number']
                    if new_company not in network.graph:
                        network.graph[new_company] = {
                            'depth': network.n+1,
                            'title': appointment['appointed_to']['company_name'],
                            'node_type': "Company",
                            'arcs': []
                        }
                    arc = {
                        'arc_type': "Appointment",
                        'start_node': officer_id
                    }
                    if arc not in network.graph[new_company]['arcs'] and network.graph[new_company]['depth'] == network.n+1:
                        network.graph[new_company]['arcs'].append(arc)
            elif len(appointments['items']) > int(self.officer_appointments_maxsize):
                network.maxsize_entities.append(dict({
                    'node':officer_id,
                    'type': 'Officer',
                    'maxsize_type': 'Appointments',
                    'size': len(appointments['items'])
                    }))
        if self.get_officer_correspondance_address:
            correspondance_address = sugartrail.api.get_correspondance_address(officer_id)
            if correspondance_address:
                new_address = sugartrail.processing.normalise_address(correspondance_address['items'][0]['address'])
                if new_address not in network.graph:
                    network.graph[new_address] = {
                        'depth': network.n+1,
                        'title': new_address,
                        'node_type': "Address",
                        'arcs': []
                    }
                arc = {
                    'arc_type': "Officer Corresponance Address",
                    'start_node': officer_id
                }
                if arc not in network.graph[new_address]['arcs'] and network.graph[new_address]['depth'] == network.n+1:
                    network.graph[new_address]['arcs'].append(arc)
        if self.get_officer_duplicates:
            duplicate_officers = sugartrail.api.get_duplicate_officers(officer_id)
            if duplicate_officers:
                if self.officer_duplicates_maxsize == None or len(duplicate_officers) < int(self.officer_duplicates_maxsize or 0):
                    for duplicate in duplicate_officers:
                        new_officer = duplicate['links']['self'].split('/')[2]
                        if new_officer not in network.graph:
                            network.graph[new_officer] = {
                                'depth': network.n+1,
                                'title': duplicate['title'],
                                'node_type': "Person",
                                'arcs': []
                            }
                        arc = {
                            'arc_type': "Duplicate Officer",
                            'start_node': officer_id
                        }
                        if arc not in network.graph[new_officer]['arcs'] and network.graph[new_officer]['depth'] == network.n+1:
                            network.graph[new_officer]['arcs'].append(arc)
                elif len(duplicate_officers) > int(self.officer_duplicates_maxsize):
                    network.maxsize_entities.append(dict({
                        'node':officer_id,
                        'type': 'Officer',
                        'maxsize_type': 'Duplicates',
                        'size': len(duplicate_officers)
                        }))

    def search_address(self, network, address, company_data):
        """Gets officers, companies and addresses connected to input officer
        (officer_id)."""
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
                            new_company = company['company_number']
                            if new_company not in network.graph:
                                network.graph[new_company] = {
                                    'depth': network.n+1,
                                    'title': company['company_name'],
                                    'node_type': "Company",
                                    'arcs': []
                                }
                            arc = {
                                'arc_type': "Company at Address",
                                'start_node': address
                            }
                            if arc not in network.graph[new_company]['arcs'] and network.graph[new_company]['depth'] == network.n+1:
                                network.graph[new_company]['arcs'].append(arc)
                    elif len(companies['items']) > int(self.companies_at_address_maxsize):
                        network.maxsize_entities.append(dict({
                            'node':address,
                            'type': 'Address',
                            'maxsize_type': 'Companies',
                            'size': len(companies['items'])
                            }))
        if self.get_officers_at_address:
            officers = sugartrail.api.get_officers_at_address(address)
            if officers:
                if self.officers_at_address_maxsize == None or len(officers) < int(self.officers_at_address_maxsize or 0):
                    for officer in officers:
                        if 'links' and 'title' in officer:
                            new_officer = officer['links']['self'].split('/')[2]
                            if new_officer not in network.graph:
                                network.graph[new_officer] = {
                                    'depth': network.n+1,
                                    'title': officer['title'],
                                    'node_type': "Person",
                                    'arcs': []
                                }
                            arc = {
                                'arc_type': "Officer at Address",
                                'start_node': address
                            }
                            if arc not in network.graph[new_officer]['arcs'] and network.graph[new_officer]['depth'] == network.n+1:
                                network.graph[new_officer]['arcs'].append(arc)
                elif len(officers) > int(self.officers_at_address_maxsize):
                    network.maxsize_entities.append(dict({
                        'node':address,
                        'type': 'Address',
                        'maxsize_type': 'Officers',
                        'size': len(officers)
                    }))
