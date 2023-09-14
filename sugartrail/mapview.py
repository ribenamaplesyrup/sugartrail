from ipywidgets import HTML, Widget, Layout, Output, VBox, HBox, Textarea
from ipyleaflet import Map, Marker, MarkerCluster, AwesomeIcon, AntPath, Popup
import functools

def build_map(network, clear_widget=True):
    """Generates map and table for displaying paths for input network data."""
    if clear_widget:
        Widget.close_all()
    m, path_table = load_map_data(network)
    return m, path_table

def load_map_data(network):
    """Adds data from input network to map in 3 layers; marker_cluster,
    address_trail and origin_trail. marker_cluster contains all the companies
    in the network geolocated, address_trail contains all the historic address
    antpaths and origin_trail contains all the antpaths connecting companies
    through other companies towards the origin company."""
    # initialise historic address trail antpath
    address_trail = AntPath(
        locations=[],
        dash_array=[1,10],
        delay=1000,
        color='#ed2f2f',
        pulse_color='#FFFFFF'
    )
    # initialise trail from company to origin antpath
    origin_trail = AntPath(
        locations=[],
        dash_array=[1,10],
        delay=1000,
        color='#000000',
        pulse_color='#FFFFFF'
    )
    # initialise table for printing company to origin trail
    path_table = HTML(
        value=""
    )
    # initialise map
    m = Map(
        center=(50, 0),
        zoom=5,
        layout=Layout(width='90%', height='650px')
    )
    # add antpath layers
    m.add_layer(address_trail)
    m.add_layer(origin_trail)
    # add marker for each company in network
    marker_cluster = MarkerCluster(
        center=(50, 0),
        markers=get_marker_data(network, address_trail, origin_trail, path_table),
        disable_clustering_at_zoom = 25,
        max_cluster_radius = 25
    )
    # add markers as layer
    m.add_layer(marker_cluster)
    return m, path_table

def get_marker_data(network,address_trail, origin_trail, path_table):
    """Generates a marker for each company historic address."""
    markers = []
    for index, row in enumerate(network.address_history):
        if row['lat'] and row['lon']:
            marker_color = "green"
            # locate company at historic address
            company = list(filter(lambda d: d.get('company_number') == row['company_number'], network.company_records))
            if company:
                company_name = company[0]['company_name']
                company_status = company[0]['company_status']
                if company_status == "active":
                    if row['end_date']:
                        marker_color = "red"
                else:
                    marker_color = "black"
                address = row['address']
                # find path from company to origin
                path = network.find_path(str(row['company_number']))
                locations_from_origin = locations_from_origin_path(path, network)
                message = HTML()
                message.value = str(company_name) + "<hr>" + str(address)
                icon = AwesomeIcon(
                    marker_color=marker_color
                )
                # find historic addresses path for company
                address_path = get_address_path(network,str(row['company_number']))
                marker = Marker(
                    icon=icon,
                    opacity=1,
                    location=(row['lat'],
                    row['lon']),
                    draggable=False,
                    popup=message,
                    title="Address"
                    )
                # attach on click behavoir for marker
                marker.on_click(functools.partial(
                    on_button_clicked,
                    address_path=address_path,
                    address_trail=address_trail,
                    path_table=path_table,
                    origin_trail=origin_trail,
                    path=path, location=(row['lat'], row['lon']),
                    locations_from_origin = locations_from_origin
                    ))
                markers.append(marker)
    return markers

def locations_from_origin_path(path, network):
    """Returns list of addresses found within origin path."""
    locations = []
    for node in path:
        if node['node_type'] == 'Company':
            # finds location for company node
            company_address_history = list(filter(lambda d: d.get('company_number') == node['id'], network.address_history))
            company_address_history_sorted = sorted(company_address_history, key=lambda d: d['start_date'], reverse=True)
            last_company_address_row = {}
            for address_row in company_address_history_sorted:
                if address_row['lat'] and address_row['lon']:
                    last_company_address_row = address_row
                    break
            if last_company_address_row:
                lat = last_company_address_row['lat']
                lon = last_company_address_row['lon']
                if not lat or not lon:
                    pass
                else:
                    locations.append([lat,lon])
        elif node['node_type'] == 'Address':
            if 'lat' in network.graph[node['id']]:
                lat = network.graph[node['id']]['lat']
                lon = network.graph[node['id']]['lon']
                locations.append([lat,lon])
            else:
                pass
    return locations

def get_address_path(network, company_id):
    """Returns list of historic addresses for input company (company_id)."""
    company_address_history = list(filter(lambda d: d.get('company_number') == company_id, network.address_history))
    company_address_history_sorted = sorted(company_address_history, key=lambda d: d['start_date'], reverse=True)
    address_path = []
    for index, row in enumerate(company_address_history_sorted):
        if not row['lat'] or not row['lon']:
            pass
        else:
            address_path.insert(0,[row['lat'], row['lon']])
    return address_path

def on_button_clicked(address_path, path, location, address_trail, path_table, origin_trail, locations_from_origin, **kwargs):
    """Adds data to map layers that will render when marker is clicked."""
    address_trail.locations = address_path
    locations_from_origin[-1] = location
    origin_trail.locations = locations_from_origin
    path_table.value = html_table_generator(path)
    return

def html_table_generator(path):
    """Generates table for displaying origin path data."""
    table_style = '<style>table {font-family: arial, sans-serif;border-collapse: collapse;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}tr:nth-child(even) {background-color: #dddddd;}</style>'
    headers = ['Node Index', 'Title', 'Depth', 'Link Type', 'Link']
    headers_row = ""
    for header in headers:
        headers_row += '<th>' + header + '</th>'
    nodes = ""
    for i, node in enumerate(path):
        nodes += '<tr><td>' + node['node_index'] + '</td><td>' + str(node['title']) + '</td><td>' + str(node['depth']) + '</td><td>' + str(node['link_type']) + '</td><td>' + str(node['link']) + '</td></tr>'
    table_html = table_style + '<table><tr>' + headers_row + '</tr>' + nodes + '</table>'
    return table_html
