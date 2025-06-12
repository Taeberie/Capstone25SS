import matplotlib.pyplot as plt
from typing import Callable
from Server import Server, calculate_metrics
import numpy as np
import matplotlib
import threading

# macOS에서 한글 폰트 설정 (윈도우는 'Malgun Gothic')
matplotlib.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

def round_robin(servers: list[Server]):
  rr_index = [0]
  def inner(_):
    s = servers[rr_index[0] % len(servers)]
    rr_index[0] += 1
    return s
  return inner

def weighted_round_robin(servers: list[Server]):
    weights = [s.bandwidth for s in servers]
    weighted_list = []
    for i, w in enumerate(weights):
        weighted_list.extend([i] * int(w))  # 가중치 비례로 인덱스 복제
    idx = [0]

    def inner(_):
        server = servers[weighted_list[idx[0] % len(weighted_list)]]
        idx[0] += 1
        return server

    return inner

def least_connections(servers: list[Server]):
  return min(servers, key=lambda s: len(s.pending_requests))

def my_optimizer(servers: list[Server]):
  return min(servers, key=lambda s: s.estimate_latency())
  
# 전체 테스트 실행 함수
def run_simulation(servers: list[Server], requests: list[float], select_fn: Callable[[list[Server]], Server]):
  for s in servers:
    s.reset()

  stop_event = threading.Event()

  # 서버별 개별 스레드로 병렬 처리
  threads: list[threading.Thread] = []
  for s in servers:
    t = threading.Thread(target=s.process, args=(stop_event,))
    t.start()
    threads.append(t)

  def send_requests():
    for size in requests:
      selected = select_fn(servers)
      selected.receive_request(size)

  request_thread = threading.Thread(target=send_requests)

  request_thread.start()
  request_thread.join()  # 요청 전송 완료 후
  stop_event.set()       # 서버 처리 루프 종료

  for t in threads:
    t.join()

  matrix = calculate_metrics(servers)
  result = [(s.avg_latency(), s.avg_time(), s.total_requests) for s in servers]

  return matrix, result

servers = [
  Server("Server1", 1000),  # 처리 속도: 1000 bytes/sec
  Server("Server2", 800),
  Server("Server3", 900),
  Server("Server4", 700)
]
requests = list(np.random.uniform(5, 10, 1000))  # 요청 크기(byte)

rr_matrix, rr_result = run_simulation(servers, requests, round_robin(servers))
wrr_matrix, wrr_result = run_simulation(servers, requests, weighted_round_robin(servers))
lc_matrix, lc_result = run_simulation(servers, requests, least_connections)
opt_matrix, opt_result = run_simulation(servers, requests, my_optimizer)

# 시각화
x = np.arange(len(servers))
width = 0.2
labels = [f"{s.name}\n처리속도: {s.bandwidth} bytes/sec" for s in servers]

plt.figure(figsize=(14, 7))
bars1 = plt.bar(x - 1.5 * width, [r[0] for r in rr_result], width, label="Round Robin")
bars2 = plt.bar(x - 0.5 * width, [w[0] for w in wrr_result], width, label="Weighted RR")
bars3 = plt.bar(x + 0.5 * width, [l[0] for l in lc_result], width, label="Least Conn")
bars4 = plt.bar(x + 1.5 * width, [o[0] for o in opt_result], width, label="Optimized")

plt.xticks(x, labels)
plt.ylabel("평균 처리 시간 (s)")
plt.title("로드밸런싱 알고리즘 비교")
plt.legend()

for idx in range(len(servers)):
  for bars, data in zip([bars1, bars2, bars3, bars4], [rr_result, wrr_result, lc_result, opt_result]):
    height = bars[idx].get_height()
    plt.text(
      bars[idx].get_x() + bars[idx].get_width()/2,
      height + 0.005,
      f"{data[idx][1]:.2f}s\n{data[idx][2]} req",
      ha='center', va='bottom', fontsize=7
    )

metrics = [
  ("Round Robin", rr_matrix),
  ("Weighted RR", wrr_matrix),
  ("Least Conn", lc_matrix),
  ("Optimized", opt_matrix)
]

text = []
for name, (lat, thr, fair) in metrics:
  text.append(f"{name}\n응답시간: {lat:.3f} sec\n처리량: {thr:.2f} req/sec\n공정성: {fair:.4f}")
  print(f"{name} = 응답시간: {lat:.3f} sec, 처리량: {thr:.2f} req/sec, 공정성: {fair:.4f}")

# 텍스트 박스 추가
plt.gcf().text(0.7, 0.5, "\n\n".join(text), fontsize=10, bbox=dict(facecolor='white', alpha=0.6))
plt.tight_layout()
plt.show()