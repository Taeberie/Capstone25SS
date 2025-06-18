import json
import matplotlib.pyplot as plt
import os

# macOS에서 한글 폰트 설정 (윈도우는 'Malgun Gothic')
plt.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

folder = "special_statistic_try/try4/"

json_path = os.path.join(folder, "stats_summary.json")

with open(json_path, "r", encoding="utf-8") as f:
    stats = json.load(f)

metrics = ["average_latency_mean", "throughput_mean", "fairness_index_mean"]
metric_labels = {
    "average_latency_mean": "평균 지연 시간 (s)",
    "throughput_mean": "초당 처리량 (req/s)",
    "fairness_index_mean": "공정성 (Jain Index)"
}

distributions = [d for d in stats.keys()]
algorithms = list(next(iter(stats.values())).keys())

visualize_folder = os.path.join(folder, "visualize")
os.makedirs(visualize_folder, exist_ok=True)

for metric in metrics:
    plt.figure(figsize=(12, 6))

    for alg in algorithms:
        y_values = [stats[dist][alg][metric] for dist in distributions]
        plt.plot(distributions, y_values, marker='o', label=alg)

    plt.title(f"요청 분포별 알고리즘 {metric_labels[metric]} 변화")
    plt.xlabel("요청 분포 유형")
    plt.ylabel(metric_labels[metric])
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(visualize_folder, f"{metric}_lineplot_special.png"))
    plt.close()


for metric in metrics:
    plt.figure(figsize=(12, 6))

    data = {alg: [stats[dist][alg][metric] for dist in distributions] for alg in algorithms}
    plt.boxplot(data.values(), tick_labels=data.keys())

    plt.title(f"요청 분포별 알고리즘 {metric_labels[metric]} 분포(Box Plot)")
    plt.xlabel("알고리즘")
    plt.ylabel(metric_labels[metric])
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(visualize_folder, f"{metric}_boxplot_special.png"))
    plt.close()
    
for dist in stats:
    print(f"\n[{dist}]")
    best = None
    best_score = float('inf')
    for algo, vals in stats[dist].items():
        latency = vals["average_latency_mean"]
        throughput = vals["throughput_mean"]
        fairness = vals["fairness_index_mean"]
        
        # 예: 가중합 점수 계산 (낮을수록 좋다고 가정)
        score = latency - 0.01 * throughput + (1 - fairness)
        if score < best_score:
            best_score = score
            best = algo
    print(f"✅ 가장 좋은 알고리즘: {best}")