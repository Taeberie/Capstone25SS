from Server import Server, calculate_metrics
from Algorithm import get_algorithm_map_default
import matplotlib.pyplot as plt
from typing import Callable
from tqdm import tqdm
import numpy as np
import matplotlib
import threading
import json
import os

# macOS에서 한글 폰트 설정 (윈도우는 'Malgun Gothic')
matplotlib.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

def run_simulation(servers: list[Server], dist: str, requests: list, algorithm: str):
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
    for i, req in enumerate(requests):
      if dist == "dynamic" and i == 50 and servers[2].bandwidth > 500:
        servers[2].bandwidth *= 0.5
      if dist == "server_specific" and req.get("preferred_server"):
        selected = next(s for s in servers if s.name == req["preferred_server"])
      else:
        selected = select_fn(servers)

      selected.receive_request(req["request_id"], req["size"])

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
  Server("Server1", 2000),  # 처리 속도: 1000 bytes/sec
  Server("Server2", 1600),
  Server("Server3", 1800),
  Server("Server4", 1400)
]
algorithm_map = get_algorithm_map_default(servers)

distributions = ["bursty", "server_specific", "dynamic"]
num_runs = 5
summary_runs = {dist: {algo: [] for algo in algorithm_map.keys()} for dist in distributions}

# Experiment meta info (use first run's config)
metainfo = {
  "title": "로드밸런싱 알고리즘 비교",
  "description": "서버별 로드밸런싱 알고리즘의 성능을 여러 요청 분포에 대해 비교",
  "servers": [{"name": s.name, "bandwidth": s.bandwidth} for s in servers],
  "algorithms": list(algorithm_map.keys()),
  "distributions": distributions,
}

for dist in distributions:
  for run in range(num_runs):
    total_request = 1000  # 각 분포별 총 요청 수
    np.random.seed(run)  # 각 실행마다 동일한 시드 사용
    metainfo["total_request"] = total_request
    # Generate request sizes based on distribution
    if dist == "bursty":
      request_sizes = []
      num = 2  # Number of bursty sub-distributions
      for _ in range(num):
        sub = np.random.randint(total_request // num // 2, total_request*3 // num // 4)
        burst = list(np.random.uniform(70, 130, sub))
        idle = [0] * (total_request // num - sub)
        request_sizes.extend(burst + idle)
      request_sizes.extend(list(np.random.uniform(70, 130, total_request % num)))
    elif dist == "server_specific":
      request_sizes = list(np.random.uniform(50, 100, total_request))
    elif dist == "dynamic":
      request_sizes = list(np.random.uniform(50, 100, total_request))
    else:
      raise ValueError(f"Unknown distribution: {dist}")

    requests = []
    for id, req in enumerate(request_sizes):
      if dist == "server_specific":
        preferred_server = "Server1" if np.random.rand() < 0.3 else None
        requests.append({
          "request_id": id + 1,
          "size": req,
          "preferred_server": preferred_server,
          "algorithm": [],
        })
      else:
        requests.append({
          "request_id": id + 1,
          "size": req,
          "algorithm": [],
        })

    for algorithm in tqdm(algorithm_map.keys(), desc=f"Running {dist} distribution, {run+1}/{num_runs} runs"):
      matrix, result = run_simulation(servers, dist, requests, algorithm)
      average_latency, throughput, fairness_index = matrix
      summary_runs[dist][algorithm].append({
        "average_latency": average_latency,
        "throughput": throughput,
        "fairness_index": fairness_index,
        "servers": [
          {
            "server": s.name,
            "bandwidth": s.bandwidth,
            "avg_latency": res[0],
            "avg_time": res[1],
            "total_requests": res[2]
          } for s, res in zip(servers, result)
        ]
      })

# Aggregate results: mean and stddev per algorithm per distribution
import statistics
stats_summary = {}
for dist in distributions:
  stats_summary[dist] = {}
  for algo in algorithm_map.keys():
    latencies = [run["average_latency"] for run in summary_runs[dist][algo]]
    throughputs = [run["throughput"] for run in summary_runs[dist][algo]]
    fairnesses = [run["fairness_index"] for run in summary_runs[dist][algo]]
    stats_summary[dist][algo] = {
      "average_latency_mean": statistics.mean(latencies),
      "average_latency_std": statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
      "throughput_mean": statistics.mean(throughputs),
      "throughput_std": statistics.stdev(throughputs) if len(throughputs) > 1 else 0.0,
      "fairness_index_mean": statistics.mean(fairnesses),
      "fairness_index_std": statistics.stdev(fairnesses) if len(fairnesses) > 1 else 0.0,
    }

# For visualization: average latency per algorithm per distribution
labels = list(algorithm_map.keys())
x = np.arange(len(labels))
width = 0.25

plt.figure(figsize=(14, 7))
colors = ['tab:blue', 'tab:orange', 'tab:green']

for i, dist in enumerate(distributions):
  means = [stats_summary[dist][algo]["average_latency_mean"] for algo in labels]
  stds = [stats_summary[dist][algo]["average_latency_std"] for algo in labels]
  plt.bar(x + width*i - width, means, width, yerr=stds, label=dist, color=colors[i], capsize=5)

plt.xticks(x, labels)
plt.ylabel("평균 응답 시간 (s)")
plt.title("알고리즘별 분포 유형에 따른 평균 응답 시간")
plt.legend(title="요청 분포")
plt.tight_layout()

idx = 1
while os.path.exists(f"./special_statistic_try/try{idx}"):
  idx += 1
folder = f"./special_statistic_try/try{idx}/"

os.makedirs(folder, exist_ok=True)
json_path = os.path.join(folder, "result.json")
img_path = os.path.join(folder, "result.png")
stats_path = os.path.join(folder, "stats_summary.json")

# Save detailed data
data = {
  "metainfo": metainfo,
  "summary_runs": summary_runs,
  "stats_summary": stats_summary,
}
with open(json_path, "w", encoding="utf-8") as f:
  json.dump(data, f, ensure_ascii=False, indent=2)

# Save stats summary separately
with open(stats_path, "w", encoding="utf-8") as f:
  json.dump(stats_summary, f, ensure_ascii=False, indent=2)

plt.savefig(img_path)
plt.close()

print(f"결과가 {folder}에 저장되었습니다.")