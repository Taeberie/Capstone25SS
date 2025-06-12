import networkx as nx

def compute_weight(delay, load, bandwidth, qos, alpha, beta, gamma):
    return alpha * delay + beta * (load / bandwidth) + gamma * (1 - qos)

def optimize_routes(G, source, target, alpha, beta, gamma):
    """
    G: DiGraph, source→target 최단 경로와 가중치 계산
    반환: (path, cost)
    """
    for u, v, data in G.edges(data=True):
        data['weight'] = compute_weight(
            data['delay'], data['load'], data['bandwidth'], data['qos'],
            alpha, beta, gamma
        )
    path = nx.dijkstra_path(G, source, target, weight='weight')
    cost = sum(G[u][v]['weight'] for u, v in zip(path, path[1:]))
    return path, cost