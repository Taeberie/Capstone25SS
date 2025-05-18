from scapy.all import rdpcap, IP, TCP, UDP
from collections import defaultdict
import pandas as pd
import numpy as np

# === 1. 설정 ===
PCAP_FILE = "vpn_traffic_20250511_163852.pcap"  # pcap 경로
OUTPUT_CSV = "session_features_iscx_format.csv"

# === 2. pcap 로드 및 세션 분류 ===
packets = rdpcap(PCAP_FILE)
sessions = defaultdict(list)

for pkt in packets:
    if IP in pkt and (TCP in pkt or UDP in pkt):
        proto = "TCP" if TCP in pkt else "UDP"
        key = (
            pkt[IP].src,
            pkt[IP].dst,
            pkt.sport,
            pkt.dport,
            proto
        )
        sessions[key].append(pkt)

# === 3. IAT 계산 함수 ===
def compute_iat_stats(times):
    if len(times) < 2:
        return {
            "total": 0, "min": 0, "max": 0, "mean": 0, "std": 0
        }
    iats = np.diff(sorted(times))
    return {
        "total": len(iats),
        "min": np.min(iats),
        "max": np.max(iats),
        "mean": np.mean(iats),
        "std": np.std(iats)
    }

# === 4. 세션 통계 피처 생성 ===
feature_list = []

for key, pkts in sessions.items():
    times = [float(pkt.time) for pkt in pkts]
    sizes = [len(pkt) for pkt in pkts]
    start_time = min(times)
    end_time = max(times)
    duration = end_time - start_time

    src_ip, dst_ip, src_port, dst_port, proto = key

    f_times, b_times = [], []
    for pkt in pkts:
        if pkt[IP].src == src_ip:
            f_times.append(float(pkt.time))
        else:
            b_times.append(float(pkt.time))

    f_iat = compute_iat_stats(f_times)
    b_iat = compute_iat_stats(b_times)
    all_iat = compute_iat_stats(times)

    flowPktsPerSecond = len(pkts) / duration if duration > 0 else 0
    flowBytesPerSecond = sum(sizes) / duration if duration > 0 else 0

    feature_list.append({
        "duration": duration,
        "total_fiat": f_iat["total"],
        "total_biat": b_iat["total"],
        "min_fiat": f_iat["min"],
        "min_biat": b_iat["min"],
        "max_fiat": f_iat["max"],
        "max_biat": b_iat["max"],
        "mean_fiat": f_iat["mean"],
        "mean_biat": b_iat["mean"],
        "flowPktsPerSecond": flowPktsPerSecond,
        "flowBytesPerSecond": flowBytesPerSecond,
        "min_flowiat": all_iat["min"],
        "max_flowiat": all_iat["max"],
        "mean_flowiat": all_iat["mean"],
        "std_flowiat": all_iat["std"]
    })

# === 5. CSV 저장 ===
df = pd.DataFrame(feature_list)
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ 저장 완료: {OUTPUT_CSV}")