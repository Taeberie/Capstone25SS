from fastapi import FastAPI, Request
import httpx, time
import joblib
import numpy as np
from collections import defaultdict, deque

# 1) 학습된 파이프라인(스케일러+imputer+XGBClassifier) 로드
vpn_pipeline = joblib.load("vpn_pipeline.joblib")

app = FastAPI()

# 2) VPN 전용/일반(non-VPN) 전용 서버 풀
vpn_server    = "http://localhost:8001"
nonvpn_server = "http://localhost:8002"

# 3) 클라이언트 IP별 최근 요청 정보 버퍼 (슬라이딩 윈도우)
WINDOW_SIZE  = 20   # 최근 20개 요청만 유지
MIN_SAMPLES  = 10   # 분류 시 최소 10개 요청 필요
flow_buffer  = defaultdict(lambda: deque(maxlen=WINDOW_SIZE))

def extract_features(buf: deque) -> np.ndarray:
    ts    = np.fromiter((t for t,_ in buf), dtype=float)
    sizes = np.fromiter((s for _,s in buf), dtype=float)
    iats  = np.diff(ts) if len(ts) >= 2 else np.array([np.nan])

    # 1) 피처 사전 미리 기본값으로 채워 두기
    feat = { name: np.nan for name in vpn_pipeline.feature_names_in_ }

    # 2) 실제 계산 가능한 피처만 덮어쓰기
    if len(ts) > 0:
        duration = ts[-1] - ts[0]
        total_iat = np.nansum(iats)
        min_iat   = np.nanmin(iats)
        max_iat   = np.nanmax(iats)
        mean_iat  = np.nanmean(iats)
        tot_bytes = np.nansum(sizes)
        bps       = tot_bytes / duration if duration > 0 else np.nan

        feat["duration"]             = duration
        feat["total_fiat"]           = total_iat
        feat["min_biat"]             = min_iat
        feat["max_fiat"]             = max_iat
        feat["max_biat"]             = max_iat
        feat["mean_fiat"]            = mean_iat
        feat["flowBytesPerSecond"]   = bps
        feat["min_flowiat"]          = min_iat
        feat["mean_flowiat"]         = mean_iat

    # 3) 파이프라인 순서에 맞춰 numpy 배열 생성
    X = np.array(
        [[feat[name] for name in vpn_pipeline.feature_names_in_]],
        dtype=float
    )
    return X

@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy(request: Request, path: str):
    global vpn_idx, normal_idx

    # 1) 타이밍·크기 정보 버퍼에 저장
    now  = time.time()
    body = await request.body()
    ip   = request.client.host
    flow_buffer[ip].append((now, len(body)))

    # 2) 충분한 샘플이 모였으면 분류, 아니면 기본(non-VPN) 처리
    if len(flow_buffer[ip]) >= MIN_SAMPLES:
        X_feat = extract_features(flow_buffer[ip])
        pred_np = vpn_pipeline.predict(X_feat)[0] # "VPN" 또는 "NonVPN"
        pred = ["NonVPN", "VPN"][int(pred_np)]
    else:
        pred = "NonVPN"
    
    # 3) VPN vs non-VPN 별 라운드로빈 서버 선택
    if pred == "VPN": target = vpn_server
    else: target = nonvpn_server

    # 4) 실제 요청 포워딩
    start = time.monotonic()
    headers = dict(request.headers)
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            request.method,
            f"{target}/{path}",
            headers=headers,
            content=body
        )
    latency = round(time.monotonic() - start, 4)
    
    print(pred)
    
    response = {
        "proxied_to": target,
        "latency":    latency,
        "vpn_pred":   pred,
        "data":       resp.json()
    }
    

    return response