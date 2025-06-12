from typing import Callable
import matplotlib.pyplot as plt
import matplotlib
import threading
import numpy as np
from Server import Server

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
  total = sum(weights)
  weight_counters = [0]

  def inner(_):
    ratio = [w / total for w in weights]
    idx = int(weight_counters[0] % 1)
    for i, r in enumerate(ratio):
      idx = i
      if weight_counters[0] < r * total:
        break
    weight_counters[0] += 1
    return servers[idx]

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

  def process_servers():
    threads = []
    for s in servers:
      t = threading.Thread(target=s.process, args=(stop_event,))
      t.start()
      threads.append(t)
    for t in threads:
      t.join()

  def send_requests():
    for size in requests:
      selected = select_fn(servers)
      selected.receive_request(size)

  process_thread = threading.Thread(target=process_servers)
  request_thread = threading.Thread(target=send_requests)

  process_thread.start()
  request_thread.start()

  request_thread.join()  # 요청 전송 완료 후
  stop_event.set()       # 서버 처리 루프 종료
  process_thread.join()

  return [(s.avg_latency(), s.avg_time(), s.total_requests) for s in servers]

servers = [
  Server("Server1", 1000),  # 처리 속도: 1000 bytes/sec
  Server("Server2", 800),
  Server("Server3", 900),
  Server("Server4", 700)
]
requests = list(np.random.uniform(5, 10, 1000))  # 요청 크기(byte)

rr = run_simulation(servers, requests, round_robin(servers))
wrr = run_simulation(servers, requests, weighted_round_robin(servers))
lc = run_simulation(servers, requests, least_connections)
opt = run_simulation(servers, requests, my_optimizer)

# 시각화
x = np.arange(len(servers))
width = 0.2
labels = [s.name for s in servers]

plt.figure(figsize=(14, 7))
bars1 = plt.bar(x - 1.5 * width, [r[0] for r in rr], width, label="Round Robin")
bars2 = plt.bar(x - 0.5 * width, [w[0] for w in wrr], width, label="Weighted RR")
bars3 = plt.bar(x + 0.5 * width, [l[0] for l in lc], width, label="Least Conn")
bars4 = plt.bar(x + 1.5 * width, [o[0] for o in opt], width, label="Optimized")

plt.xticks(x, labels)
plt.ylabel("평균 처리 시간 (s)")
plt.title("로드밸런싱 알고리즘 비교")
plt.legend()

for idx in range(len(servers)):
  for bars, data in zip([bars1, bars2, bars3, bars4], [rr, wrr, lc, opt]):
    height = bars[idx].get_height()
    plt.text(
      bars[idx].get_x() + bars[idx].get_width()/2,
      height + 0.005,
      f"{data[idx][1]:.2f}s\n{data[idx][2]} req",
      ha='center', va='bottom', fontsize=7
    )

plt.tight_layout()
plt.show()

