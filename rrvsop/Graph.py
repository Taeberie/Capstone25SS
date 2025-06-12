import networkx as nx
import matplotlib.pyplot as plt
import matplotlib

# macOS에서 한글 폰트 설정 (윈도우는 'Malgun Gothic')
matplotlib.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

G = nx.DiGraph()

# 노드 추가
nodes = ["A", "R1", "LB", "S1", "S2"]
G.add_nodes_from(nodes)

# 링크 추가 (지연 시간 또는 가중치)
edges = [
    ("A", "R1", {"delay": 5}),
    ("R1", "LB", {"delay": 3}),
    ("LB", "S1", {"delay": 2}),
    ("LB", "S2", {"delay": 4}),
]
G.add_edges_from(edges)

# 시각화
pos = {
    "A": (0, 2),
    "R1": (1, 2),
    "LB": (2, 2),
    "S1": (3, 3),
    "S2": (3, 1),
}
edge_labels = nx.get_edge_attributes(G, 'delay')
nx.draw(G, pos, with_labels=True, node_color='lightgreen', node_size=1000)
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
plt.title("로드밸런서 포함 네트워크 구성")
plt.show()