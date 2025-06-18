import math
import random
import numpy as np
from Server import Server
from typing import Callable

algorithm = []

def round_robin(servers: list[Server]) -> Callable[[list[Server]], Server]:
  rr_index = [0]
  def inner(_) -> Server:
    s = servers[rr_index[0] % len(servers)]
    rr_index[0] += 1
    return s
  return inner

def least_connections(servers: list[Server]) -> Server:
  return min(servers, key=lambda s: len(s.pending_requests))

def min_latency_scheduling(servers: list[Server]) -> Server:
  return min(servers, key=lambda s: s.estimate_latency())

def adaptive_weighted_flowaware_balancer(servers, alpha=1.0, beta=1.0, w1=1.0, w2=0.5, w3=0.5):
    def softmax(scores: list[float], beta: float = 1.0) -> list[float]:
      max_score = max(scores)
      exps = [math.exp(beta * (s - max_score)) for s in scores]
      total = sum(exps)
      return [x / total for x in exps]
    
    total_requests = sum(s.total_requests for s in servers) + 1e-6
    scores = []
    for s in servers:
        latency = s.estimate_latency()
        fairness_penalty = s.total_requests / total_requests
        score = -(w1 * latency + w2 * len(s.pending_requests) + w3 * fairness_penalty)
        scores.append(score)
    probs = softmax(scores, beta)
    return random.choices(servers, weights=probs, k=1)[0]
  
def multi_factor_optimizer(servers: list[Server]) -> Server:
    total_requests = sum(s.total_requests for s in servers)

    # 가중치 설정 (알파: 지연, 베타: 공정성, 감마: 처리속도)
    alpha = 0.6
    beta = 0.3
    gamma = 0.1

    def cost(s: Server) -> float:
        latency = s.estimate_latency()
        fairness_penalty = (s.total_requests / total_requests)**2 if total_requests > 0 else 0
        bandwidth_penalty = 1 / s.bandwidth if s.bandwidth > 0 else float('inf')
        return alpha * latency + beta * fairness_penalty + gamma * bandwidth_penalty

    return min(servers, key=cost)

def get_algorithm_map(
  RoundRobin: bool,
  LeastConnection: bool,
  MinLatencyScheduling: bool,
  AdaptiveWeightedFlowawareBalancer: bool,
  MultiFactorOptimizer: bool,
  servers: list[Server]
  ):
  algorithm_map = {}
  if RoundRobin:
    algorithm_map["RR"] = round_robin(servers)
  if LeastConnection:
    algorithm_map["LC"] = least_connections
  if MinLatencyScheduling:
    algorithm_map["MLS"] = min_latency_scheduling
  if AdaptiveWeightedFlowawareBalancer:
    algorithm_map["AWFB"] = adaptive_weighted_flowaware_balancer
  if MultiFactorOptimizer:
    algorithm_map["MFO"] = multi_factor_optimizer
  if not algorithm_map:
    raise ValueError("At least one algorithm must be selected.")
  return algorithm_map

def get_algorithm_map_default(servers: list[Server]):
  """기본 알고리즘 맵을 반환합니다."""
  return get_algorithm_map(True, True, True, True, True, servers)