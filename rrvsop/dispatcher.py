import socket, json
from Server import Server, calculate_metrics
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import threading
import time

# macOS에서 한글 폰트 설정 (윈도우는 'Malgun Gothic')
matplotlib.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

# ---- 알고리즘 구현 ----
def round_robin(servers):
    idx = [0]
    def inner(_):
        s = servers[idx[0] % len(servers)]
        idx[0] += 1
        return s
    return inner

def weighted_round_robin(servers):
    weights = [s.bandwidth for s in servers]
    weighted_list = []
    for i, w in enumerate(weights):
        weighted_list.extend([i] * int(w))
    idx = [0]
    def inner(_):
        server = servers[weighted_list[idx[0] % len(weighted_list)]]
        idx[0] += 1
        return server
    return inner

def least_connections(servers):
    # 실제 요청 큐 길이 기반
    return min(servers, key=lambda s: len(s.pending_requests))

def my_optimizer(servers):
    # 예시: 추정 레이턴시 기반
    return min(servers, key=lambda s: s.estimate_latency())

def jains_fairness(values):
    values = np.array(values)
    numerator = np.sum(values) ** 2
    denominator = len(values) * np.sum(values ** 2)
    if denominator == 0:
        return 1.0
    return numerator / denominator

# ---- 서버 구조 및 상태 ----
servers = [
    Server("S1", 1000),
    Server("S2", 800),
    Server("S3", 900)
]

# 알고리즘 셀렉터 준비
selector_rr = round_robin(servers)
selector_wrr = weighted_round_robin(servers)
# least_connections/my_optimizer는 함수형

# 각 서버의 요청 기록 및 결과 누적
results_rr = []
results_wrr = []
results_lc = []
results_opt = []
num_requests = 0
VISUALIZE_EVERY = 20

start_time = time.time()

# 소켓 설정
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.bind(("0.0.0.0", 9999))
print("[Python] Listening for NS3 requests...")

def record_metrics(servers):
    """서버별 (평균레이턴시, 평균처리시간, 총요청수) 튜플 반환"""
    return [(s.avg_latency(), s.avg_time(), s.total_requests) for s in servers]

def visualize(rr, wrr, lc, opt):
    x = np.arange(len(servers))
    width = 0.2
    labels = [f"{s.name}\n처리속도: {s.bandwidth} bytes/sec" for s in servers]

    fig = plt.figure(figsize=(14, 7))

    # Histogram for average latency per server per algorithm
    ax1 = fig.add_subplot(121)
    latency_rr = [r[0] for r in rr]
    latency_wrr = [w[0] for w in wrr]
    latency_lc = [l[0] for l in lc]
    latency_opt = [o[0] for o in opt]

    bar1 = ax1.bar(x - 1.5 * width, latency_rr, width, label="Round Robin")
    bar2 = ax1.bar(x - 0.5 * width, latency_wrr, width, label="Weighted RR")
    bar3 = ax1.bar(x + 0.5 * width, latency_lc, width, label="Least Conn")
    bar4 = ax1.bar(x + 1.5 * width, latency_opt, width, label="Optimized")

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylabel("평균 처리 시간 (s)")
    ax1.set_title("서버별 평균 레이턴시 분포")
    ax1.legend()

    for idx in range(len(servers)):
        for bars, data in zip([bar1, bar2, bar3, bar4], [rr, wrr, lc, opt]):
            height = bars[idx].get_height()
            ax1.text(
                bars[idx].get_x() + bars[idx].get_width()/2,
                height + 0.005,
                f"{data[idx][1]:.2f}s\n{data[idx][2]} req",
                ha='center', va='bottom', fontsize=7
            )

    # Summary table in top-right corner
    ax2 = fig.add_subplot(122)
    ax2.axis('off')

    total_runtime = time.time() - start_time
    # Calculate throughput per algorithm (total requests / runtime)
    throughput_rr = sum([r[2] for r in rr]) / total_runtime if total_runtime > 0 else 0
    throughput_wrr = sum([w[2] for w in wrr]) / total_runtime if total_runtime > 0 else 0
    throughput_lc = sum([l[2] for l in lc]) / total_runtime if total_runtime > 0 else 0
    throughput_opt = sum([o[2] for o in opt]) / total_runtime if total_runtime > 0 else 0

    # Jain's fairness index for average latency (lower latency is better, but fairness on latency means fairness on values, so invert latency to fairness metric)
    # To avoid division by zero or negative values, add small epsilon
    eps = 1e-6
    fairness_rr = jains_fairness([1/(lat + eps) for lat in latency_rr])
    fairness_wrr = jains_fairness([1/(lat + eps) for lat in latency_wrr])
    fairness_lc = jains_fairness([1/(lat + eps) for lat in latency_lc])
    fairness_opt = jains_fairness([1/(lat + eps) for lat in latency_opt])

    col_labels = ["알고리즘", "평균 처리 시간 (s)", "처리량 (req/s)", "Jain's 공정성 지표"]
    row_labels = ["Round Robin", "Weighted RR", "Least Conn", "Optimized"]

    table_vals = [
        [f"{np.mean(latency_rr):.3f}", f"{throughput_rr:.2f}", f"{fairness_rr:.3f}"],
        [f"{np.mean(latency_wrr):.3f}", f"{throughput_wrr:.2f}", f"{fairness_wrr:.3f}"],
        [f"{np.mean(latency_lc):.3f}", f"{throughput_lc:.2f}", f"{fairness_lc:.3f}"],
        [f"{np.mean(latency_opt):.3f}", f"{throughput_opt:.2f}", f"{fairness_opt:.3f}"],
    ]

    table = ax2.table(cellText=table_vals,
                      rowLabels=row_labels,
                      colLabels=col_labels,
                      loc='center',
                      cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    ax2.set_title("알고리즘 요약 통계", fontsize=12, pad=20)

    plt.tight_layout()
    plt.show()

# 서버별 요청 큐 동작을 시뮬레이션
stop_event = threading.Event()
threads = []
for s in servers:
    t = threading.Thread(target=s.process, args=(stop_event,))
    t.daemon = True
    t.start()
    threads.append(t)

try:
    while True:
        data, addr = recv_sock.recvfrom(1024)
        req = json.loads(data.decode())
        print("[Python] Received:", req)
        req_size = req.get("size", 10)
        num_requests += 1

        # 모든 알고리즘 적용
        # 1. RR
        s_rr = selector_rr(servers)
        s_rr.receive_request(req_size)
        # 2. WRR
        s_wrr = selector_wrr(servers)
        s_wrr.receive_request(req_size)
        # 3. LC
        s_lc = least_connections(servers)
        s_lc.receive_request(req_size)
        # 4. Optimizer
        s_opt = my_optimizer(servers)
        s_opt.receive_request(req_size)

        # 결과 기록 (누적된 상태 반영)
        rr_metrics = record_metrics(servers)
        wrr_metrics = record_metrics(servers)
        lc_metrics = record_metrics(servers)
        opt_metrics = record_metrics(servers)
        results_rr = rr_metrics
        results_wrr = wrr_metrics
        results_lc = lc_metrics
        results_opt = opt_metrics

        # NS-3 라우터로 결과 전송 제거

        # 일정 요청마다 시각화
        if num_requests % VISUALIZE_EVERY == 0:
            print("[Python] Visualizing results after", num_requests, "requests")
            visualize(results_rr, results_wrr, results_lc, results_opt)
except KeyboardInterrupt:
    stop_event.set()
    for t in threads:
        t.join()
