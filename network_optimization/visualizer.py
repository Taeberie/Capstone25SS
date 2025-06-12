import matplotlib.pyplot as plt
import networkx as nx

def plot_topology(G, allocation=None):
    pos = nx.spring_layout(G)
    plt.figure(figsize=(6, 4))
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=800)
    labels = {(u, v): round(d.get('weight', 0), 2)
              for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.title("Network Topology")
    plt.axis('off')

    if allocation:
        plt.figure(figsize=(4, 3))
        servers = list(allocation.keys())
        flows   = [allocation[s] for s in servers]
        plt.bar(servers, flows)
        plt.ylabel("Allocated Traffic")
        plt.title("Load Balancer Allocation")
    plt.show()