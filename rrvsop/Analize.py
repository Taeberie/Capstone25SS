import json
import matplotlib.pyplot as plt

# macOS에서 한글 폰트 설정 (윈도우는 'Malgun Gothic')
plt.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

with open("try/try6/stats_summary.json", "r", encoding="utf-8") as f:
    stats = json.load(f)

metrics = ["average_latency_mean", "throughput_mean", "fairness_index_mean"]
metric_labels = {
    "average_latency_mean": "평균 지연 시간 (s)",
    "throughput_mean": "초당 처리량 (req/s)",
    "fairness_index_mean": "공정성 (Jain Index)"
}

# 'exponential' 분포 제외
distributions = [d for d in stats.keys() if d != "exponential"]
algorithms = list(next(iter(stats.values())).keys())

for metric in metrics:
    plt.figure(figsize=(12, 6))

    for alg in algorithms:
        y_values = [stats[dist][alg][metric] for dist in distributions]
        plt.plot(distributions, y_values, marker='o', label=alg)

    plt.title(f"[Exponential 제외] 요청 분포별 알고리즘 {metric_labels[metric]} 변화")
    plt.xlabel("요청 분포 유형")
    plt.ylabel(metric_labels[metric])
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{metric}_lineplot_no_exp.png")
    plt.close()