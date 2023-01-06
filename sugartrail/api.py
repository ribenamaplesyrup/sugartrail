import requests
import time
import os
import config

access_token = ""
# username = config.config.APIKEY
username = ""
password = ""
size = "5000"
basic_auth = requests.auth.HTTPBasicAuth(username, password)

def test():
    url = "https://api.company-information.service.gov.uk/advanced-search/companies"
    response = requests.get(url, auth=basic_auth)
    if response.status_code == 200:
        return True
    else:
        return False

def make_request(url, input, input_type, response_type):
    if basic_auth.username:
        time.sleep(0.5)
        try:
            response = requests.get(url, auth=basic_auth)
            response.raise_for_status()
            # print("here")
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as err:
            # print (err, f"{os.linesep}Failed to get {response_type} for {input_type}:", str(input))
            return
        except requests.exceptions.HTTPError as errh:
            # print (errh, f"{os.linesep}Failed to get {response_type} for {input_type}:", str(input))
            return
        except requests.exceptions.ConnectionError as errc:
            # print (errc, f"{os.linesep}Failed to get {response_type} for {input_type}:", str(input))
            return
        except requests.exceptions.Timeout as errt:
            # print (errt, f"{os.linesep}Failed to get {response_type} for {input_type}:", str(input))
            return
    else:
        print("Authentication required")

def get_company_officers(company_id):
    url = "https://api.company-information.service.gov.uk/company/" + company_id + "/officers"
    return make_request(url, company_id, 'company', 'officers')

def get_psc(company_id):
    url = "https://api.company-information.service.gov.uk/company/" + company_id + "/persons-with-significant-control"
    return make_request(url, company_id, 'company', 'psc')

def get_company(company_id):
    url = "https://api.company-information.service.gov.uk/company/" + company_id
    return make_request(url, company_id, 'company', 'company')

def get_address_changes(company_id):
    url = "https://api.company-information.service.gov.uk/company/" + str(company_id) + "/filing-history/?category=address"
    return make_request(url, company_id, 'company', 'address history')

def get_correspondance_address(officer_id):
    url = "https://api.company-information.service.gov.uk/officers/" + officer_id + "/appointments?size=" + size
    return make_request(url, officer_id, 'officer', 'correspondance address')

def get_appointments(officer_id):
    url = "https://api.company-information.service.gov.uk/officers/" + officer_id + "/appointments"
    return make_request(url, officer_id, 'officer', 'appointments')

def get_duplicate_officers(officer_id):
    url = "https://api.company-information.service.gov.uk/officers/" + officer_id + "/appointments"
    response = make_request(url, officer_id, 'officer', 'appointments')
    if response:
        officer_data = response
        officer_self_link = response['links']['self']
        name_list = officer_data['name'].replace(',','').split(' ')
        name = " ".join(name_list[1:]) + " " + name_list[0]
        url = "https://api.company-information.service.gov.uk/search/officers?q=" + name
        response = make_request(url, name, 'officer name', 'officers')
        filtered_results = []
        if response:
            if 'items' in response:
                for officer in response['items']:
                    if 'date_of_birth' in officer.keys() and 'date_of_birth' in officer_data.keys():
                        if officer['date_of_birth'] == officer_data['date_of_birth'] and officer['links']['self'] != officer_self_link:
                            filtered_results.append(officer)
                return filtered_results
            else:
                return

def get_companies_at_address(address):
    url = "https://api.company-information.service.gov.uk/advanced-search/companies?location=" + address + "&size=" + "5000"
    return make_request(url, address, 'address', 'companies')

def get_officers_at_address(address):
    url = "https://api.company-information.service.gov.uk/search/officers?q=location:" + address
    response = make_request(url, address, 'address', 'officers')
    if response:
        if 'items' in response:
            officers = []
            word_list = []
            for word in address.replace(',','').split():
                word_list.append(word)
            for officer in response['items']:
                if all(word in officer['address_snippet'] for word in word_list):
                    officers.append(officer)
            return officers
