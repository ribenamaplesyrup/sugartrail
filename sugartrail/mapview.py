from ipywidgets import HTML, Widget, Layout, Output, VBox, HBox, Textarea
from ipyleaflet import Map, Marker, MarkerCluster, AwesomeIcon, AntPath, Popup
import pandas as pd
from datetime import datetime
import functools
from string import ascii_lowercase as alc

def build_map(network):
    Widget.close_all()
    m, path_table = load_map_data(network)
    return m, path_table

def get_address_path(network, company_id):
    company_address_history = network.address_history.loc[network.address_history['company_number'] == company_id]
    address_path = []
    for index, row in company_address_history.iterrows():
        address_path.insert(0,[row['lat'], row['lon']])
    return address_path

def locations_from_origin_path(path, network):
    locations = []
    for node in path:
        if node['type'] == 'Company':
            last_company_address_row = network.address_history.loc[network.address_history['company_number'] == node['id']].iloc[:1]
            lat = last_company_address_row['lat'].item()
            lon = last_company_address_row['lon'].item()
            locations.append([float(lat),float(lon)])
        elif node['type'] == 'Address':
            address_row = network.addresses.loc[network.addresses['address'] == node['node']].iloc[:1]
            lat = address_row['lat'].item()
            lon = address_row['lon'].item()
            locations.append([float(lat),float(lon)])
    return locations

def on_button_clicked(address_path, path, location, address_trail, path_table, origin_trail, locations_from_origin, **kwargs):
    address_trail.locations = address_path
    locations_from_origin[-1] = location
    origin_trail.locations = locations_from_origin
    path_table.value = html_table_generator(path)
    return

def html_table_generator(path):
    table_style = '<style>table {font-family: arial, sans-serif;border-collapse: collapse;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}tr:nth-child(even) {background-color: #dddddd;}</style>'
    headers = ['Node Index', 'Node', 'Hop', 'Node Type', 'Link']
    headers_row = ""
    for header in headers:
        headers_row += '<th>' + header + '</th>'
    nodes = ""
    for i, node in enumerate(path):
        nodes += '<tr><td>' + node['node_index'] + '</td><td>' + str(node['node']) + '</td><td>' + str(node['hop']) + '</td><td>' + str(node['node_type']) + '</td><td>' + str(node['link']) + '</td></tr>'
    table_html = table_style + '<table><tr>' + headers_row + '</tr>' + nodes + '</table>'
    return table_html

def load_map_data(network):
    address_trail = AntPath(
    locations=[],
    dash_array=[1,10],
    delay=1000,
    color='#ed2f2f',
    pulse_color='#FFFFFF'
    )
    origin_trail = AntPath(
    locations=[],
    dash_array=[1,10],
    delay=1000,
    color='#000000',
    pulse_color='#FFFFFF'
    )
    path_table = HTML(
    value=""
    )
    m = Map(center=(50, 0),
            zoom=5,
            layout=Layout(width='90%', height='650px'))
    m.add_layer(address_trail)
    m.add_layer(origin_trail)
    marker_cluster = MarkerCluster(
        center=(50, 0),
        markers=get_marker_data(network, address_trail, origin_trail, path_table),
        disable_clustering_at_zoom = 25,
        max_cluster_radius = 25
    )
    m.add_layer(marker_cluster)
    return m, path_table

def get_marker_data(network,address_trail, origin_trail, path_table):
    address_trail=address_trail
    origin_trail=origin_trail
    ms = []
    for index, row in network.address_history.iterrows():
        path = ""
        locations_from_origin = ""
        message = HTML()
        marker_color = "green"
        company = network.companies.loc[network.companies['company_number'] == row['company_number']]
        company_name = company['company_name'].item()
        company_status = company['company_status'].item()
        if company_status == "active":
            if row['end_date'] != None:
                marker_color = "red"
        else:
            marker_color = "black"
        address = row['address']
        path = network.find_path(str(row['company_number']))
        locations_from_origin = locations_from_origin_path(path, network)
        message.value = str(company_name) + "<hr>" + str(address)
        icon = AwesomeIcon(
        marker_color=marker_color
        )
        address_path = get_address_path(network,str(row['company_number']))
        marker = Marker(icon=icon, opacity=1, location=(row['lat'], row['lon']), draggable=False, popup=message, title="Address")
        marker.on_click(functools.partial(on_button_clicked, address_path=address_path, address_trail=address_trail, path_table=path_table, origin_trail=origin_trail, path=path, location=(row['lat'], row['lon']), locations_from_origin = locations_from_origin))
        ms.append(marker)
    return ms
