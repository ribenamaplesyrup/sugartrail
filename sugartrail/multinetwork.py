import IPython
import os
import sugartrail

def find_network_connections(first_network, second_network, max_depth=5, print_progress=False):
    """Returns a list of nodes connecting ."""
    hops = 0
    while hops < max_depth:
        first_network.progress.pre_print = str(hops) + "/" + str(max_depth) + " hops completed."
        second_network.progress.pre_print = str(hops) + "/" + str(max_depth) + " hops completed."
        if first_network.n < hops:
            first_network.perform_hop(1, print_progress=print_progress)
        if second_network.n < hops:
            second_network.perform_hop(1, print_progress=print_progress)
        hops += 1
        IPython.display.clear_output(wait=True)
        connectors = [x for x in list(filter(first_network.graph.__contains__, second_network.graph.keys())) if x]
        if connectors:
            print("Found connection(s)!")
            return connectors
        print(str(hops) + "/" + str(max_depth) + " hops completed.")
    print("No connections found.")
    return

def load_multiple_networks(networks_dir):
    """Loads multiple network files from a directory into a list"""
    entity_graphs = []
    for filename in os.listdir(networks_dir):
        if filename.endswith('.json'):
            network = sugartrail.base.Network(file=f'{networks_dir}/{filename}')
            entity_graphs.append(network)
    return entity_graphs

def find_multi_network_connections(networks: list):
    """Finds the shortest paths connecting 2+ networks from a list of networks,
    returning nodes within these found paths."""
    s_path_network = []
    for i, entity in enumerate(networks):
        for j in range(i+1,len(networks)):
            connections = [(x, networks[i].graph[x]['depth']+networks[j].graph[x]['depth']) for x in list(filter(networks[i].graph.__contains__, networks[j].graph.keys())) if x]
            sorted_data = sorted(connections, key=lambda x: x[1])
            filtered_data = [x[0] for x in list(filter(lambda x: x[1] == sorted_data[0][1], sorted_data))]
            for connection in filtered_data:
                for entity_graph in [networks[i], networks[j]]:
                    for node in entity_graph.find_path(connection):
                        network_node = {'title': node['title'],
                                         'node_type': node['node_type'],
                                         'id': node['id'],
                                         'link_type': node['link_type'],
                                         'link' : "",
                                         'depth': node['depth']
                                        }
                        if node['link']:
                            for link in [x.strip() for x in node['link'].split(',')]:
                                new_node = network_node.copy()
                                new_node['link'] = next((item['id'] for item in entity_graph.find_path(connection) if item["node_index"] == link), None)
                                if new_node not in s_path_network:
                                    s_path_network.append(new_node)
                        else:
                            new_node = network_node.copy()
                            s_path_network.append(new_node)
    return s_path_network
