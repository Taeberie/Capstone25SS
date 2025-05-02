# Capstone25SS
# **목적**
**목적지 IP나 애플리케이션 별 부하 측정하여 로드밸런싱 알고리즘 개발**

## 데이터 분류 다시 할 것
라벨링된 데이터에서 VPN / NON-VPN 라벨 분포마다 이상치 처리

## ISCX 데이터셋 이용 이유
1. 실제와 유사한 네트워크 환경
2. 다양한 프로토콜과 패턴 사용
3. 라벨링된 데이터셋 지도학습 가능

## 주요 트래픽 유형 및 애플리케이션
- 브라우징(Browsing): Firefox와 Chrome을 사용한 HTTPS 트래픽
- 이메일(Email): Thunderbird 클라이언트를 사용하여 SMTP/S, POP3/SSL, IMAP/SSL 프로토콜을 통한 이메일 트래픽
- 채팅(Chat): Facebook, Hangouts, Skype, AIM, ICQ 등의 인스턴트 메시징 애플리케이션
- 스트리밍(Streaming): YouTube(HTML5 및 Flash 버전)와 Vimeo를 통한 멀티미디어 스트리밍
- 파일 전송(File Transfer): Skype 파일 전송, SFTP(SSH를 통한 FTP), FTPS(SSL을 통한 FTP)
- VoIP: Facebook, Hangouts, Skype를 통한 음성 통화
- P2P: uTorrent와 Transmission을 사용한 BitTorrent 트래픽

    출처 : https://www.unb.ca/cic/datasets/ids.html
---
## ISCX VPN-nonVPN 데이터셋 활용 전략
A1, A2, B 시나리오 중 A1, A2 시나리오만 이용

**B는 혼합 환경으로 조건이 다양하여 분석이 힘들고 실험적인 설정일 수 있음**

| 시나리오 | 설명 | 부하 측정 및 최적화에 적합도 | 사용 추천도 |
|----------|------|-------------------------------|--------------|
| **Browsing** | 브라우저 기반 웹 탐색 (Chrome, Firefox 등) | 다양한 목적지 IP와 트래픽 패턴 존재 | ✅ 매우 추천 |
| **Streaming** | YouTube 등 스트리밍 활동 | 고용량 트래픽 집중 발생 | ✅ 매우 추천 |
| **VoIP** | Skype 등 음성 통화 | 실시간성 테스트 가능, 고빈도 패킷 | ✅ 추천 |
| **Email** | Gmail, YahooMail 등 이메일 | 트래픽 양이 작고 간헐적 | ❌ 비추천 |
| **Chat** | Facebook Chat, Hangout 등 | 실시간성은 있으나 부하가 낮음 | ⚠️ 보조 용도 |
| **VPN** | 위 모든 활동을 VPN 통해 수행 | 목적지 IP 왜곡, 부하 집중 현상 분석용 | ✅ 분석 보조 |

---

## 모든 시나리오 이용 ❌
1. **Streaming + Browsing + VoIP** 중심으로 선택
2. VPN/Non-VPN 버전을 **비교용으로 병행 사용**
3. 애플리케이션(Label) 기준으로 **정제 및 시각화**

---

## 시나리오 필터링

```python
import pandas as pd

# 데이터 불러오기
df = pd.read_csv("ISCX_VPN_nonVPN.csv")

# Streaming, Browsing, VoIP 시나리오만 필터링
filtered_df = df[df['Label'].str.contains("Streaming|Browsing|VoIP", case=False)]

# VPN 여부 구분
vpn_df = filtered_df[filtered_df['Label'].str.contains("VPN", case=False)]
nonvpn_df = filtered_df[~filtered_df['Label'].str.contains("VPN", case=False)]

# 목적지 IP별 트래픽 합산
ip_traffic = nonvpn_df.groupby('Destination IP')['Bytes'].sum().sort_values(ascending=False)
print(ip_traffic.head(10))
```

# 로드 밸런싱 알고리즘
| 알고리즘 이름                   | 특징                                            | 한계점                                                  |
|-------------------------------|-------------------------------------------------|----------------------------------------------------------|
| **Round Robin**               | 순차적으로 요청을 분배                          | 서버 부하를 고려하지 않음                               |
| **Least Connection**          | 가장 적은 연결 수를 가진 서버에 분배            | 연결 수가 실제 부하를 반영하지 않을 수 있음             |
| **Weighted Round Robin**      | 서버 성능에 따라 가중치 적용                    | 고정 가중치일 경우 동적 부하 변화에 취약                |
| **Weighted Least Connection** | 가중치를 적용한 최소 연결 방식                  | 가중치 설정이 복잡할 수 있음                            |
| **IP Hashing**                | 클라이언트 IP로 해시하여 고정 서버에 분배       | 특정 서버로 트래픽 쏠림 가능성 (비균형)                 |
| **Random**                    | 무작위로 서버를 선택                            | 분산이 비효율적일 수 있음                               |
| **Consistent Hashing**        | 노드 변경에도 해시 값 유지                      | 구현 복잡도 높음, 데이터 불균형 발생 가능               |
| **Resource-Aware**            | 실시간 CPU, 메모리, 네트워크 사용률 기반 분배   | 모니터링 오버헤드 발생, 예측 오류 가능성                |

## 추가로 해야할 일
간단한 로드 밸런싱 알고리즘을 구현해보며 시뮬레이션 실행