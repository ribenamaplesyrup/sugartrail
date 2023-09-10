import sugartrail
import pytest
import json

# test 1: network initialised without auth and without arguments:

def test_init_without_arguments(capsys):
    sugartrail.base.Network()
    captured = capsys.readouterr()
    assert captured.out == 'No input provided. Please provide either officer_id, company_id, address or file as input.\n'

# test 2: network initialised without auth and with arguments prints auth requirement:

def test_init_officer_without_auth(capsys):
    sugartrail.base.Network(officer_id = '_')
    captured = capsys.readouterr()
    assert captured.out == 'Authentication required\n'

def test_init_company_without_auth(capsys):
    sugartrail.base.Network(company_id = '_')
    captured = capsys.readouterr()
    assert captured.out == 'Authentication required\n'

def test_init_address_without_auth(capsys):
    sugartrail.base.Network(address = '_')
    captured = capsys.readouterr()
    assert captured.out == 'Authentication required\n'

# test 3: network initialised without auth and with arguments remains stateless:

def test_empty_officer_without_auth(capsys):
    network = sugartrail.base.Network(officer_id = '_')
    assert network._officer_id == None

def test_empty_company_without_auth(capsys):
    network = sugartrail.base.Network(company_id = '_')
    assert network._company_id == None

def test_empty_address_without_auth(capsys):
    network = sugartrail.base.Network(address = '_')
    assert network._address == None

# test 4: network initialised with 'file' arg without auth loads network:

def test_file_init_without_auth():
    network = sugartrail.base.Network(file ='./assets/networks/domain_corp_network.json')
    with open('./assets/networks/domain_corp_network.json') as f:
        network_json = json.load(f)
    for key in network.__dict__.keys():
        if key not in ['hop', '_file', 'progress']:
            assert network.__dict__[key] == network_json[key]

# test 5: network loads network from file without auth:

def test_file_load_without_auth():
    network = sugartrail.base.Network()
    network.load('./assets/networks/domain_corp_network.json')
    with open('./assets/networks/domain_corp_network.json') as f:
        network_json = json.load(f)
    for key in network.__dict__.keys():
        if key not in ['hop', '_file', 'progress']:
            assert network.__dict__[key] == network_json[key]
