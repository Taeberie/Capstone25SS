import yaml
import networkx as nx

def create_network_graph(path="config.yaml"):
    """
    config.yaml에서 물리 토폴로지를 읽어 NetworkX DiGraph 생성
    """
    cfg = yaml.safe_load(open(path))
    G = nx.DiGraph()
    for edge in cfg['edges']:
        u, v = edge['from'], edge['to']
        G.add_edge(u, v,
                   delay=edge['delay'],
                   load=edge['load'],
                   bandwidth=edge['bandwidth'],
                   qos=edge['qos'])
    return G