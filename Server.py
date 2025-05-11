from fastapi import FastAPI, Request
from user_agents import parse
import psutil

app = FastAPI()

@app.get("/")
async def root(request: Request):
  headers = dict(request.headers)
  client_ip = request.headers.get("x-forwarded-for") or request.client.host
  user_agent_str = headers.get("user-agent", "")
  user_agent = parse(user_agent_str)

  info = {
    "ip": client_ip,
    "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
    "os": f"{user_agent.os.family} {user_agent.os.version_string}",
    "device": f"{user_agent.device.family}",
    "is_mobile": user_agent.is_mobile,
    "is_tablet": user_agent.is_tablet,
    "is_pc": user_agent.is_pc,
    "is_bot": user_agent.is_bot,
  }

  return info

@app.get("/health")
def health():
  return {"cpu": psutil.cpu_percent(interval=0.1)}