from scapy.all import rdpcap, IP, TCP, UDP
import pandas as pd

# (1) pcap 파일 경로
packets = rdpcap("vpn환경_traffic캡처/vpn_traffic_20250511_163852.pcap")

# (2) 피처 추출
data = []
for pkt in packets:
    if IP in pkt:
        row = {
            "src_ip": pkt[IP].src,
            "dst_ip": pkt[IP].dst,
            "proto": pkt[IP].proto,
            "length": len(pkt),
            "is_tcp": int(pkt.haslayer(TCP)),
            "is_udp": int(pkt.haslayer(UDP)),
            "src_port": pkt[TCP].sport if pkt.haslayer(TCP) else (pkt[UDP].sport if pkt.haslayer(UDP) else None),
            "dst_port": pkt[TCP].dport if pkt.haslayer(TCP) else (pkt[UDP].dport if pkt.haslayer(UDP) else None),
            "tcp_flags": str(pkt[TCP].flags) if pkt.haslayer(TCP) else None,
        }
        data.append(row)

# (3) 데이터프레임으로 변환 및 CSV 저장
df = pd.DataFrame(data)
df.to_csv("vpn환경_traffic캡처/vpn_features_20250511.csv", index=False)

print("✅ Features saved to vpn_features_20250511.csv")