import yaml
from graph_model import create_network_graph
from optimizer import optimize_routes
from flow_optimizer import optimize_load_balancing
from visualizer import plot_topology
from ns3_simulator import simulate_allocation

def main():
    cfg = yaml.safe_load(open("network_optimization/config.yaml"))
    alpha, beta, gamma = cfg['alpha'], cfg['beta'], cfg['gamma']
    demand            = cfg['demand']
    capacities        = cfg['capacities']

    G = create_network_graph("network_optimization/config.yaml")

    servers = list(capacities.keys())
    costs, paths = {}, {}
    for srv in servers:
        path, cost = optimize_routes(G, 'LoadBalancer', srv,
                                     alpha, beta, gamma)
        costs[srv], paths[srv] = cost, path
        print(f"{srv}: path={path}, cost={cost:.3f}")

    allocation = optimize_load_balancing(costs, capacities, demand)
    print("\nOptimal Allocation:", allocation)

    plot_topology(G)
    plot_topology(G, allocation)

    simulate_allocation(allocation, paths)

if __name__ == "__main__":
    main()