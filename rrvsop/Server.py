from threading import Event
import time
import numpy as np

# 서버 클래스 정의
class Server:
  def __init__(self, name, bandwidth):
    self.name = name
    self.bandwidth = bandwidth  # 처리 속도 (bytes/sec)
    self.pending_requests = []  # 처리 중인 요청들 (각 요청은 남은 처리 시간)
    self.max_latency = 0
    self.total_latency = 0
    self.total_requests = 0
    self.total_time = 0
    self.result = []  # 결과 저장용

  def receive_request(self, id, size):
    """요청이 서버에 도착하면 대기열에 추가 (요청 시간, 남은 처리 시간) 튜플로 저장"""
    processing_time = size / self.bandwidth
    self.pending_requests.append([time.time(), processing_time, id])

  def process(self, stop_event: Event):
    """요청들을 순차적으로 실제 처리 시간 기준으로 처리"""
    
    while not (stop_event.is_set() and not self.pending_requests):
      if not self.pending_requests:
        time.sleep(0.001)
        continue
      start = time.time()
      
      # 대기 중인 요청 중 첫 번째 요청을 처리
      start_time, duration, id = self.pending_requests.pop(0)
      time.sleep(duration)  # 실제 처리 시간만큼 대기
      elapsed = time.time() - start_time
      elapsed = max(elapsed, 0)  # 음수 시간 방지
      
      self.max_latency = max(self.max_latency, elapsed)
      self.total_latency += elapsed
      self.total_requests += 1
      
      end = time.time()
      self.result.append((id, self.name, elapsed, end - start))
      self.total_time += end - start

  def estimate_latency(self):
    """현재 대기 중인 요청의 남은 처리 시간의 합 기반 예측"""
    return sum(req[1] for req in self.pending_requests)

  def avg_latency(self):
    if self.total_requests == 0:
      return 0
    return self.total_latency / self.total_requests
  
  def avg_time(self):
    if self.total_requests == 0:
      return 0
    return self.total_time / self.total_requests

  def reset(self):
    self.pending_requests = []  # 처리 중인 요청들 (각 요청은 남은 처리 시간)
    self.max_latency = 0
    self.total_latency = 0
    self.total_requests = 0
    self.total_time = 0
    self.result = []  # 결과 저장용

def calculate_metrics(servers: list[Server]):
  # 요청 수, 평균 응답 시간, 총 처리 시간 수집
  request_counts = [s.total_requests for s in servers]
  avg_latencies = [s.avg_latency() for s in servers]
  total_times = [s.total_time for s in servers]

  # 평균 응답 시간 (서버 평균)
  average_latency = np.mean(avg_latencies)

  # 전체 처리량 (총 요청 수 / 평균 시간)
  total_requests = sum(request_counts)
  total_elapsed_time = max(total_times)
  throughput = total_requests / total_elapsed_time if total_elapsed_time > 0 else 0

  # Jain’s Fairness Index
  numerator = total_requests ** 2
  denominator = len(servers) * sum(r**2 for r in request_counts)
  jain_index = numerator / denominator if denominator > 0 else 0

  return average_latency, throughput, jain_index