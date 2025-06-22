import json
import os

folder_path = "./try/try18"

# 결과 파일 로드
with open(os.path.join(folder_path, "result.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

summary = data["summary"]

best_algo = None
best_score = float("inf")
algorithm = []

for algo, res in summary.items():
    latency = res["average_latency"]
    throughput = res["throughput"]
    fairness = res["fairness_index"]

    # 점수 계산: 낮을수록 좋음 (가중치는 상황에 따라 조정 가능)
    score = latency - throughput + (1 - fairness)

    algorithm.append((algo, latency, throughput, fairness, score))
    if score < best_score:
        best_score = score
        best_algo = algo

algorithm.sort(key=lambda x: x[4])  # 점수 기준으로 정렬
print(f"폴더 경로: {folder_path}")
print(f"✅ 알고리즘 비교 결과 (총 {len(algorithm)}개 알고리즘):")
for algo, latency, throughput, fairness, score in algorithm:
    print(f"  - {algo}: 평균 응답 시간 = {latency:.3f} s, 초당 처리량 = {throughput:.2f} req/s, 공정성 = {fairness:.4f}, 점수 = {score:.4f}")

print("\n✅ 알고리즘병 점수 비교 결과:")
for idx, (algo, latency, throughput, fairness, score) in enumerate(algorithm, start=1):
    print(f"{idx}. {algo} (점수: {score:.4f})")
print(f"\n최고의 알고리즘은 '{best_algo}'입니다. (점수: {best_score:.4f})")
