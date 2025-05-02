# 가상의 서버 IP 목록
servers = ['192.168.1.1', '192.168.1.2', '192.168.1.3']
server_index = 0

assigned_requests = []

for _, row in requests.iterrows():
    assigned_ip = servers[server_index]
    assigned_requests.append((row['Timestamp'], row['App'], row['Size'], assigned_ip))
    server_index = (server_index + 1) % len(servers)  # 다음 서버로

assigned_df = pd.DataFrame(assigned_requests, columns=['Timestamp', 'App', 'Size', 'Assigned_IP'])