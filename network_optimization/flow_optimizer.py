import networkx as nx

def optimize_load_balancing(costs, capacities, demand):
    """
    costs: dict {server: cost_i}
    capacities: dict {server: C_i}
    demand: 총 트래픽량 D
    반환: dict {server: allocation f_i}
    """
    G = nx.DiGraph()
    # super-source → LoadBalancer
    G.add_edge('source', 'LoadBalancer', capacity=demand, weight=0)
    # LoadBalancer → 서버들 + 서버 → super-sink
    for srv, cost in costs.items():
        G.add_edge('LoadBalancer', srv,
                   capacity=capacities[srv], weight=cost)
        G.add_edge(srv, 'sink', capacity=capacities[srv], weight=0)
    flow_dict = nx.min_cost_flow(G, 'source', 'sink')
    alloc = flow_dict['LoadBalancer']
    return {srv: alloc.get(srv, 0) for srv in costs}