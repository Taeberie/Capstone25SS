import math
import random
import numpy as np
from Server import Server

algorithm = []

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

def min_latency_scheduling(servers: list[Server]):
  return min(servers, key=lambda s: s.estimate_latency())

def hybrid_load_balancing(servers: list[Server]):
  weighted_score = []
  for srv in servers:
    # 연결수 가중치(40%) + 응답시간 가중치(60%)
    score = 0.4*len(srv.pending_requests) + 0.6*srv.avg_time()
    weighted_score.append(score)
  return servers[np.argmin(weighted_score)]

def awfb_scheduling(servers: list[Server], alpha: float = 1.0, beta: float = 1.0) -> Server:
  def compute_score(server: Server, alpha: float = 1.0) -> float:
    latency = server.estimate_latency()
    return 1 / (latency + alpha * len(server.pending_requests) + 1e-6)

  def softmax(scores: list[float], beta: float = 1.0) -> list[float]:
    max_score = max(scores)
    exps = [math.exp(beta * (s - max_score)) for s in scores]
    total = sum(exps)
    return [x / total for x in exps]

  scores = [compute_score(s, alpha) for s in servers]
  probs = softmax(scores, beta)
  selected = random.choices(servers, weights=probs, k=1)[0]
  return selected
  
def my_optimizer(servers: list[Server]):
  def cost(s: Server):
    # 가중치를 적절히 조절 (ex: latency 중심이면 w1 높게)
    w1 = 0.6  # 대기 시간
    w2 = 0.4  # 요청 수 기반 공정성

    waiting = s.estimate_latency()  # 예상 대기 시간
    fairness = s.total_requests  # 요청이 많은 서버는 불이익
    return w1 * waiting + w2 * fairness

  return min(servers, key=cost)

def get_algorithm_map(
  RoundRobin: bool,
  WeightedRR: bool,
  LeastConnection: bool,
  MinLatencyScheduling: bool,
  HybridLoadBalancing: bool,
  MyOptimizer: bool,
  AWFB: bool,
  servers: list[Server]
  ):
  algorithm_map = {}
  if RoundRobin:
    algorithm_map["Round Robin"] = round_robin(servers)
  if WeightedRR:
    algorithm_map["Weighted RR"] = weighted_round_robin(servers)
  if LeastConnection:
    algorithm_map["Least Conn"] = least_connections
  if MinLatencyScheduling:
    algorithm_map["MLS"] = min_latency_scheduling
  if HybridLoadBalancing:
    algorithm_map["HLB"] = hybrid_load_balancing
  if MyOptimizer:
    algorithm_map["My Optimizer"] = my_optimizer
  if AWFB:
    algorithm_map["AWFB"] = awfb_scheduling
  if not algorithm_map:
    raise ValueError("At least one algorithm must be selected.")
  return algorithm_map

def get_algorithm_map_default(servers: list[Server]):
  """기본 알고리즘 맵을 반환합니다."""
  return {
    "Round Robin": round_robin(servers),
    "Weighted RR": weighted_round_robin(servers),
    "Least Conn": least_connections,
    "MLS": min_latency_scheduling,
    "HLB": hybrid_load_balancing,
    "My Optimizer": my_optimizer,
    "AWFB": awfb_scheduling,
  }