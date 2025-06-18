from Server import Server, calculate_metrics
from Algorithm import get_algorithm_map_default
import matplotlib.pyplot as plt
from typing import Callable
import numpy as np
import matplotlib
import threading
import json
import os

# macOS에서 한글 폰트 설정 (윈도우는 'Malgun Gothic')
matplotlib.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

def run_simulation(servers: list[Server], request_sizes: list[float], requests: list, algorithm: str):
  global algorithm_map
  select_fn: Callable[[list[Server]], Server] = algorithm_map[algorithm]
  if select_fn is None:
    raise ValueError(f"알고리즘 '{algorithm}'이(가) 정의되지 않았습니다.")
  
  # 서버 초기화
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
    for id, size in enumerate(request_sizes):
      selected = select_fn(servers)
      selected.receive_request(id+1, size)

  request_thread = threading.Thread(target=send_requests)

  request_thread.start()
  request_thread.join()  # 요청 전송 완료 후
  stop_event.set()       # 서버 처리 루프 종료

  for t in threads:
    t.join()
  
  for server in servers:
    result = server.result
    for req_id, server_name, latency, time in result:
      requests[req_id - 1]["algorithm"].append({
        "name": algorithm,
        "server": server_name,
        "latency": latency,
        "time": time
      })
      
  matrix = calculate_metrics(servers)
  summary = [(s.avg_latency(), s.avg_time(), s.total_requests) for s in servers]
  
  return matrix, summary

servers = [
  Server("Server1", 1000),  # 처리 속도: 1000 bytes/sec
  Server("Server2", 800),
  Server("Server3", 900),
  Server("Server4", 700)
]

algorithm_map = get_algorithm_map_default(servers)
request_sizes = list(np.random.uniform(50, 100, 1000))  # 요청 크기(byte)

metainfo = {
  "title": "로드밸런싱 알고리즘 비교",
  "description": "서버별 로드밸런싱 알고리즘의 성능을 비교합니다.",
  "servers": [{"name": s.name, "bandwidth": s.bandwidth} for s in servers],
  "total_request": len(request_sizes),
  "algorithms": list(algorithm_map.keys()),
}

requests = []
for id, req in enumerate(request_sizes):
  requests.append({
    "request_id": id + 1,
    "size": req,
    "algorithm": [],
  })

summary = {}
for algorithm in algorithm_map.keys():
  matrix, result = run_simulation(servers, request_sizes, requests, algorithm)
  average_latency, throughput, fairness_index = matrix
  summary[algorithm] = {
    "average_latency": average_latency,
    "throughput": throughput,
    "fairness_index": fairness_index
  }
  summary[algorithm]["servers"] = []
  for s, res in zip(servers, result):
    summary[algorithm]["servers"].append(
      {
        "server": s.name,
        "bandwidth": s.bandwidth,
        "avg_latency": res[0],
        "avg_time": res[1],
        "total_requests": res[2]
      }
    )

data = {
  "metainfo": metainfo,
  "requests": requests,
  "summary": summary,
}

# 시각화
x = np.arange(len(servers))
num_algorithms = len(summary)
width = 0.8 / num_algorithms  # 전체 너비 안에서 균등 분배
offsets = np.linspace(-width * (num_algorithms - 1) / 2, width * (num_algorithms - 1) / 2, num_algorithms)

labels = [f"{s.name}\nBandwidth: {s.bandwidth} bytes/sec" for s in servers]

plt.figure(figsize=(14, 7))

bars = []
for idx, (algorithm, res) in enumerate(summary.items()):
  label = f"{algorithm:5} = Latency: {res['average_latency']:.3f} sec, Throughput: {res['throughput']:.2f} req/sec, Fairness: {res['fairness_index']:.4f}"
  print(label)
  bar = plt.bar(x + offsets[idx], [s["avg_latency"] for s in res["servers"]], width, label=label)
  bars.append(bar)

max_latency = max(max([s["avg_latency"] for s in res["servers"]]) for res in summary.values())
plt.xticks(x, labels)
plt.ylabel("Average Latency (seconds)")
plt.ylim(0, max_latency * 1.5)
plt.title("Load Balancing Algorithm Comparison")
plt.legend(loc="upper left", prop={'family': 'monospace'})

def get_fontsize_by_algorithm_count(n):
  if n <= 3: return 10
  elif n <= 5: return 9
  elif n <= 7: return 8
  elif n <= 9: return 7
  return 6

fontsize = get_fontsize_by_algorithm_count(num_algorithms)
for idx in range(len(servers)):
  for bar, server in zip(bars, summary.values()):
    height = bar[idx].get_height()
    plt.text(
      bar[idx].get_x() + bar[idx].get_width()/2,
      height + height * 0.02 + 0.01,
      f"{server["servers"][idx]["avg_time"]:.2f}s\n{server["servers"][idx]["total_requests"]} req",
      ha='center', va='bottom', fontsize=fontsize
    )
plt.tight_layout()

idx = 1
while os.path.exists(f"./try/try{idx}"):
  idx += 1
folder = f"./try/try{idx}/"

os.makedirs(folder, exist_ok=True)
json_path = os.path.join(folder, "result.json")
img_path = os.path.join(folder, "result.png")

with open(json_path, "w", encoding="utf-8") as f:
  json.dump(data, f, ensure_ascii=False, indent=2)

plt.savefig(img_path)
plt.close()

print(f"결과가 {folder}에 저장되었습니다.")