from fastapi import FastAPI, Request
import httpx, asyncio, time

app = FastAPI()

# 초기 서버 상태 (처리 중 요청 수, 평균 응답 시간)
backend_servers = ["http://localhost:8001", "http://localhost:8002", "http://localhost:8003"]
server_state = {s: {"inflight": 0, "avg_latency": 0.1} for s in backend_servers}
alpha = 0.2  # 지수이동평균 가중치

def score(server):
    state = server_state[server]
    return state["inflight"] + state["avg_latency"]  # 낮을수록 우선

@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy(request: Request, path: str):
    # 1. 가장 여유 있는 서버 선택
    print(server_state)
    target = min(backend_servers, key=score)
    server_state[target]["inflight"] += 1
    start = time.monotonic()

    try:
        body = await request.body()
        headers = dict(request.headers)

        async with httpx.AsyncClient() as client:
            response = await client.request(
                request.method,
                f"{target}/{path}",
                headers=headers,
                content=body
            )

        elapsed = time.monotonic() - start

        # 2. 지수이동평균으로 latency 갱신
        prev = server_state[target]["avg_latency"]
        server_state[target]["avg_latency"] = (1 - alpha) * prev + alpha * elapsed

        return {
            "proxied_to": target,
            "latency": round(elapsed, 4),
            "current_state": server_state[target],
            "data": response.json()
        }

    finally:
        server_state[target]["inflight"] -= 1