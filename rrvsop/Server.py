import time

# 서버 클래스 정의
class Server:
  def __init__(self, name, bandwidth):
    self.name = name
    self.bandwidth = bandwidth  # 처리 속도 (bytes/sec)
    self.pending_requests = []  # 처리 중인 요청들 (각 요청은 남은 처리 시간)
    self.total_latency = 0
    self.total_requests = 0
    self.total_time = 0

  def receive_request(self, size=1):
    """요청이 서버에 도착하면 대기열에 추가 (요청 시간, 남은 처리 시간) 튜플로 저장"""
    processing_time = size / self.bandwidth
    self.pending_requests.append([time.time(), processing_time])

  def process(self, stop_event):
    """요청들을 순차적으로 실제 처리 시간 기준으로 처리"""
    
    while not (stop_event.is_set() and not self.pending_requests):
      if not self.pending_requests:
        time.sleep(0.001)
        continue
      start = time.time()
      start_time, duration = self.pending_requests.pop(0)
      time.sleep(duration)  # 실제 처리 시간만큼 대기
      self.total_latency += (time.time() - start_time)
      self.total_requests += 1
      end = time.time()
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
    self.pending_requests = []
    self.total_latency = 0
    self.total_requests = 0