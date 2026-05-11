# e-stock-pipeline

한국투자증권 KIS Open API, Kafka, Airflow, PostgreSQL, MinIO를 활용한 주식 데이터 파이프라인 프로젝트입니다.

현재 목표는 다음과 같습니다.

```text
KIS WebSocket 실시간 데이터
→ Kafka raw topic
→ MinIO raw 저장
→ raw 메시지 분류
→ trade 메시지만 parsed topic으로 전달
→ PostgreSQL 저장
→ 이후 Spark 처리 확장
```

현재 단계에서는 Spark 처리 전까지의 실시간 수집 파이프라인을 구성하고 있습니다.

---

## 1. 현재 구성 요소

```text
Windows 개발 환경
Docker Desktop
Docker Compose
Airflow
Kafka
Kafka UI
PostgreSQL
MinIO
KIS Open API
```

각 역할은 다음과 같습니다.

```text
KIS WebSocket
→ 한국투자증권 실시간 주식 데이터 수신

Kafka
→ 실시간 메시지 버퍼 및 분기 처리

MinIO
→ S3 대체 오픈소스 오브젝트 스토리지
→ raw JSONL 파일 저장

PostgreSQL
→ 현재가, OHLCV, 이후 parsed trade 데이터 저장

Airflow
→ REST API 배치 수집, DAG 기반 작업 실행

Spark
→ 이후 대량 파일 처리, Parquet 변환, 집계 처리 예정
```

---

## 2. 폴더 구조

현재 기준 폴더 구조는 다음과 같습니다.

```text
app/
└── estock/
    ├── clients/
    │   └── kis_client.py
    │
    ├── repositories/
    │   ├── stock_current_price_repository.py
    │   └── stock_ohlcv_repository.py
    │
    ├── services/
    │   └── stock_price_service.py
    │
    ├── storage/
    │   ├── __init__.py
    │   └── minio_storage.py
    │
    └── kafka/
        ├── __init__.py
        ├── producer.py
        ├── consumer.py
        ├── topics.py
        ├── kis_message_classifier.py
        ├── kis_trade_parser.py
        │
        ├── producers/
        │   ├── __init__.py
        │   ├── test_kafka_producer.py
        │   └── kis_ws_trade_producer.py
        │
        └── consumers/
            ├── __init__.py
            ├── test_kafka_consumer.py
            ├── kis_trade_minio_consumer.py
            ├── kis_trade_raw_debug_consumer.py
            ├── kis_trade_raw_to_parsed_consumer.py
            └── kis_trade_parsed_debug_consumer.py
```

---

## 3. 폴더별 역할

### `clients/`

외부 API 호출 담당입니다.

```text
kis_client.py
→ KIS REST API 호출
→ access_token 발급 및 캐싱
→ WebSocket approval_key 발급
→ 현재가 API 호출
→ OHLCV API 호출
```

---

### `repositories/`

PostgreSQL 저장 담당입니다.

```text
stock_current_price_repository.py
→ 현재가 저장

stock_ohlcv_repository.py
→ 일봉/주봉/월봉/년봉 OHLCV 저장
```

DAG 기준이 아니라 DB 테이블/도메인 기준으로 repository를 분리합니다.

---

### `services/`

API 호출, 파싱, 저장 흐름을 조립하는 계층입니다.

```text
stock_price_service.py
→ KIS API 호출
→ 응답 데이터 처리
→ repository 호출
```

---

### `storage/`

파일 저장소 관련 코드입니다.

```text
minio_storage.py
→ MinIO 클라이언트 생성
→ 버킷 생성
→ 텍스트/JSONL 업로드
```

MinIO는 Kafka 자체가 아니라 저장소이므로 `kafka/` 밖에 둡니다.

---

### `kafka/`

Kafka 관련 공통 코드와 실행 프로그램을 모아둔 영역입니다.

```text
producer.py
→ Kafka Producer 생성 공통 함수

consumer.py
→ Kafka Consumer 생성 공통 함수

topics.py
→ Kafka topic 이름 상수 관리

kis_message_classifier.py
→ KIS WebSocket raw_message 분류

kis_trade_parser.py
→ KIS 실시간 체결 메시지 파싱
```

---

### `kafka/producers/`

Kafka에 메시지를 발행하는 실행 프로그램입니다.

```text
test_kafka_producer.py
→ Kafka 송신 테스트용 Producer

kis_ws_trade_producer.py
→ KIS WebSocket 수신 후 Kafka raw topic 발행
```

---

### `kafka/consumers/`

Kafka에서 메시지를 읽는 실행 프로그램입니다.

```text
test_kafka_consumer.py
→ Kafka 수신 테스트용 Consumer

kis_trade_minio_consumer.py
→ Kafka 메시지를 MinIO JSONL 파일로 저장

kis_trade_raw_debug_consumer.py
→ kis.stock.trade.raw topic 메시지 디버깅

kis_trade_raw_to_parsed_consumer.py
→ raw topic에서 trade 메시지만 parsed topic으로 전달

kis_trade_parsed_debug_consumer.py
→ parsed topic 메시지 디버깅
```

---

## 4. Docker Compose 실행 방식

Windows PowerShell 기준으로 실행합니다.

이 프로젝트에서는 `.env.dev`와 `.env`를 함께 사용합니다.

```powershell
docker compose --env-file .env.dev --env-file .env up -d --build
```

상태 확인:

```powershell
docker compose --env-file .env.dev --env-file .env ps
```

로그 확인:

```powershell
docker compose --env-file .env.dev --env-file .env logs --tail=50
```

컨테이너 내부 명령 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler bash
```

Python 모듈 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m 모듈경로
```

---

## 5. 주요 서비스 접속 정보

### Airflow

```text
http://localhost:18080
```

### Kafka UI

```text
http://localhost:18081
```

### MinIO Console

```text
http://localhost:19001
```

기본 개발 계정 예시:

```text
ID: minioadmin
PW: minioadmin123
```

### MinIO API

```text
localhost:19000
```

컨테이너 내부에서는 다음 주소를 사용합니다.

```text
minio:9000
```

---

## 6. 환경변수 예시

`.env.dev` 또는 `.env`에 다음 값들이 필요합니다.

```env
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka-1:29092
KAFKA_SOURCE_TOPIC=kis.stock.trade.raw

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=stock-data
MINIO_SECURE=false

# KIS REST API
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret

# KIS WebSocket
KIS_WS_URL=ws://ops.koreainvestment.com:21000
KIS_WS_STOCK_CODES=005930,000660
```

주의:

```text
.env
.env.dev
.env.prod
```

위 파일에는 API Key, Secret이 들어갈 수 있으므로 GitHub에 올리지 않습니다.

`.gitignore`에 포함하는 것을 권장합니다.

```gitignore
.env
.env.dev
.env.prod
```

---

## 7. Kafka Topic

현재 사용하는 주요 topic은 다음과 같습니다.

```text
test-stock-prices
→ Kafka 송수신 테스트용 topic

kis.stock.trade.raw
→ KIS WebSocket 원문 메시지 저장 topic

kis.stock.trade.parsed
→ KIS 실시간 체결 데이터 파싱 결과 topic
```

`app/estock/kafka/topics.py`에서 관리합니다.

```python
TEST_STOCK_PRICES = "test-stock-prices"

KIS_STOCK_TRADE_RAW = "kis.stock.trade.raw"
KIS_STOCK_TRADE_PARSED = "kis.stock.trade.parsed"
```

---

## 8. 현재까지 검증된 흐름

### 8.1 Kafka 테스트 송수신

Producer 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.producers.test_kafka_producer
```

Consumer 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.consumers.test_kafka_consumer
```

검증 결과:

```text
test_kafka_producer
→ test-stock-prices topic
→ test_kafka_consumer
```

정상 수신 확인 완료.

---

### 8.2 Python → MinIO 업로드

테스트 파일 업로드 성공.

```text
stock-data/test/...
```

MinIO 콘솔에서 파일 확인 완료.

---

### 8.3 Kafka → MinIO 저장

Consumer 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.consumers.kis_trade_minio_consumer
```

Producer 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.producers.test_kafka_producer
```

검증 결과:

```text
Kafka topic
→ kis_trade_minio_consumer
→ MinIO JSONL 저장
```

저장 경로 예시:

```text
stock-data/
└── raw/
    └── kis/
        └── trade/
            └── dt=YYYY-MM-DD/
                └── hour=HH/
                    └── kafka-trade-YYYYMMDD-HHMMSS.jsonl
```

---

### 8.4 KIS WebSocket → Kafka raw topic

Producer 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.producers.kis_ws_trade_producer
```

검증된 로그 예시:

```text
[KIS WS Producer Start]
topic       : kis.stock.trade.raw
stock_codes : ['005930', '000660']

[SUBSCRIBED] stock_code=005930
[SUBSCRIBED] stock_code=000660

[PRODUCED] topic=kis.stock.trade.raw, message_type=control_json
[PINGPONG] received and pong sent
```

현재까지 확인된 메시지:

```json
{
  "source": "KIS",
  "market": "KRX",
  "tr_id": "H0STCNT0",
  "received_at": "2026-05-11T19:10:38.910768+09:00",
  "raw_message": "{\"header\":{\"tr_id\":\"H0STCNT0\",\"tr_key\":\"005930\",\"encrypt\":\"N\"},\"body\":{\"rt_cd\":\"0\",\"msg_cd\":\"OPSP0000\",\"msg1\":\"SUBSCRIBE SUCCESS\"}}"
}
```

의미:

```text
KIS WebSocket 연결 성공
종목 구독 성공
Kafka raw topic 발행 성공
```

---

### 8.5 KIS raw message 디버깅

Debug Consumer 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.consumers.kis_trade_raw_debug_consumer
```

확인된 message_type:

```text
control_json
pingpong
```

예시:

```text
[message_type]
pingpong

[raw_message]
{"header":{"tr_id":"PINGPONG","datetime":"20260511192459"}}
```

---

### 8.6 raw → parsed Consumer

Consumer 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.consumers.kis_trade_raw_to_parsed_consumer
```

현재 장외 시간 기준 로그:

```text
[START] KIS trade raw → parsed consumer
[SOURCE TOPIC] kis.stock.trade.raw
[TARGET TOPIC] kis.stock.trade.parsed

[SKIP] offset=0, message_type=control_json
[SKIP] offset=1, message_type=control_json
[SKIP] offset=2, message_type=pingpong
```

의미:

```text
control_json은 skip
pingpong은 skip
trade 메시지만 parsed topic으로 발행 예정
```

현재 장외 시간이라 실제 trade 메시지는 아직 미확인입니다.

---

## 9. KIS raw message 분류 기준

`kis_message_classifier.py`에서 raw_message를 분류합니다.

현재 분류값:

```text
control_json
→ SUBSCRIBE SUCCESS 같은 JSON 제어 메시지

pingpong
→ KIS WebSocket heartbeat 메시지

trade
→ H0STCNT0 실시간 체결 데이터

empty
→ 빈 메시지

unknown
→ 아직 알 수 없는 메시지
```

현재까지 실제 확인된 값:

```text
control_json
pingpong
```

장중 실제 체결 데이터가 들어오면 다음 형태일 가능성이 있습니다.

```text
0|H0STCNT0|...|005930^...
```

이 경우 `trade`로 분류되어야 합니다.

---

## 10. 현재까지 완료된 것

현재까지 완료된 항목은 다음과 같습니다.

```text
1. Docker Desktop 기반 로컬 개발 환경 구성
2. Docker Compose 기반 Airflow/Kafka/PostgreSQL/MinIO 실행
3. Kafka Producer 공통 모듈 작성
4. Kafka Consumer 공통 모듈 작성
5. Kafka 테스트 Producer/Consumer 검증
6. MinIO Python 업로드 검증
7. Kafka → MinIO JSONL 저장 검증
8. KIS WebSocket approval_key 자동 발급
9. KIS WebSocket 연결 성공
10. KIS 종목 구독 성공
11. KIS WebSocket → Kafka raw topic 발행 성공
12. PINGPONG 처리 추가
13. raw_message 분류 기능 추가
14. control_json / pingpong skip 처리
15. raw → parsed Consumer 구조 준비
```

---

## 11. 아직 남은 것

Spark 처리 전까지 남은 작업은 다음과 같습니다.

```text
1. 장중 실제 trade 메시지 수신 확인
2. H0STCNT0 실시간 체결 데이터 raw 샘플 확보
3. kis_trade_parser.py 필드 매핑 확정
4. kis.stock.trade.parsed topic 데이터 검증
5. parsed topic → PostgreSQL 저장 Consumer 작성
6. stock_trade_repository.py 작성
7. Docker Compose 서비스로 Producer/Consumer 상시 실행 등록
8. 에러 topic 또는 dead-letter topic 추가
9. 장 시작/장 종료 운영 전략 정리
10. 이후 Spark로 raw JSONL/Parquet 처리 확장
```

---

## 12. 현재 진행률

대략적인 진행률은 다음과 같이 판단합니다.

```text
로컬 Docker 환경 구축: 90%
Kafka 기본 구조: 85%
MinIO 저장 구조: 85%
KIS WebSocket 연결: 80~90%
KIS raw 수집 파이프라인: 70~80%
raw message 분류: 80%
실제 체결 데이터 파싱: 20%
PostgreSQL 실시간 적재: 0~20%
Spark 연계: 0~5%
```

전체적으로 Spark 전 단계 기준으로는 약 60~65% 정도 진행된 상태로 봅니다.

---

## 13. 현재 아키텍처

```text
KIS WebSocket
    ↓
estock.kafka.producers.kis_ws_trade_producer
    ↓
Kafka topic: kis.stock.trade.raw
    ↓
┌──────────────────────────────────────┐
│                                      │
│  kis_trade_minio_consumer             │
│  → MinIO raw JSONL 저장               │
│                                      │
│  kis_trade_raw_to_parsed_consumer     │
│  → control_json / pingpong skip       │
│  → trade만 parsed topic으로 발행       │
│                                      │
└──────────────────────────────────────┘
    ↓
Kafka topic: kis.stock.trade.parsed
    ↓
향후 PostgreSQL 저장
    ↓
향후 Spark 처리
```

---

## 14. 자주 사용하는 명령어

### 전체 실행

```powershell
docker compose --env-file .env.dev --env-file .env up -d --build
```

### 상태 확인

```powershell
docker compose --env-file .env.dev --env-file .env ps
```

### KIS WebSocket Producer 실행

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.producers.kis_ws_trade_producer
```

### raw debug Consumer 실행

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.consumers.kis_trade_raw_debug_consumer
```

### raw → parsed Consumer 실행

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.consumers.kis_trade_raw_to_parsed_consumer
```

### parsed debug Consumer 실행

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.consumers.kis_trade_parsed_debug_consumer
```

### Kafka → MinIO Consumer 실행

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.consumers.kis_trade_minio_consumer
```

---

## 15. 현재 주의사항

### 1. 장외 시간에는 실시간 체결 데이터가 안 올 수 있음

현재까지 받은 메시지는 대부분 다음과 같습니다.

```text
SUBSCRIBE SUCCESS
PINGPONG
```

이는 정상입니다.

실제 체결 데이터는 장중에 확인해야 합니다.

---

### 2. PINGPONG은 Kafka에 저장하지 않음

Producer에서 PINGPONG 메시지를 받으면 다음처럼 처리합니다.

```text
PINGPONG 수신
→ websocket.pong() 응답
→ Kafka 발행하지 않음
```

이유는 PINGPONG은 데이터가 아니라 연결 유지용 메시지이기 때문입니다.

---

### 3. raw 데이터는 MinIO에 저장

원천 메시지는 MinIO에 JSONL 형태로 저장합니다.

```text
raw/kis/trade/dt=YYYY-MM-DD/hour=HH/...
```

---

### 4. PostgreSQL에는 parsed 데이터만 저장 예정

실시간 tick raw 전체를 PostgreSQL에 무작정 넣기보다, MinIO에 raw를 저장하고 PostgreSQL에는 파싱된 조회용 데이터를 저장하는 방향입니다.

---

## 16. 다음 작업

다음 작업은 장중에 실제 trade 메시지를 확보하는 것입니다.

장중 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.producers.kis_ws_trade_producer
```

동시에 raw debug Consumer 실행:

```powershell
docker compose --env-file .env.dev --env-file .env exec airflow-scheduler python -m estock.kafka.consumers.kis_trade_raw_debug_consumer
```

실제 trade 메시지가 확인되면 `kis_trade_parser.py`의 필드 매핑을 확정합니다.

예상 목표:

```text
raw_message
→ stock_code
→ trade_time
→ current_price
→ price_change
→ change_rate
→ trade_volume
→ accumulated_volume
→ accumulated_trading_value
```

이후 parsed topic을 PostgreSQL에 저장하는 Consumer를 작성합니다.
