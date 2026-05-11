# e-stock-pipeline

주식 시세 데이터를 수집·처리하는 데이터 파이프라인 학습 프로젝트.
Kafka, Airflow, PostgreSQL 을 활용한 실시간/배치 통합 환경.

## 1. 프로젝트 개요

### 목표
- 한국투자증권(KIS) Open API 로 실 주식 시세 수집
- Airflow 로 주기적 API 호출 + Kafka 로 실시간 스트리밍
- PostgreSQL 에 적재 후 LLM 컨텍스트로 활용 (장기 목표)

### 데이터 흐름

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Airflow    │───▶│    Kafka     │───▶│  PostgreSQL  │───▶│ LLM 컨텍스트  │
│              │    │              │    │              │    │              │
│ 주기적        │    │ 실시간        │    │ raw → cleaned│    │ 정제 데이터로 │
│ KIS API 호출  │    │ 메시지 버퍼   │    │ → mart 변환   │    │ 답변 퀄리티   │
│              │    │              │    │              │    │ 향상 (RAG)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

## 2. 기술 스택

| 컴포넌트     | 버전                        | 역할                                     |
| ----------- | -------------------------- | --------------------------------------- |
| Confluent   | `7.7.1`                    | Kafka + Zookeeper                       |
| Kafka UI    | `kafbat/kafka-ui:v1.1.0`   | 토픽/메시지 모니터링                       |
| PostgreSQL  | `postgres:15.17-alpine`    | 데이터 적재 + Airflow 메타DB              |
| Airflow     | `2.10.0` (Python 3.11)     | 워크플로우 오케스트레이션                  |
| kafka-python| `2.0.2`                    | Producer/Consumer 클라이언트              |
| psycopg2    | `2.9.9`                    | PostgreSQL 드라이버                      |

## 3. 폴더 구조

```
e-stock-pipeline/
├── docker-compose.yml          # 인프라 정의 (zookeeper, kafka, postgres, airflow)
├── Dockerfile                  # Airflow 커스텀 이미지 (kafka-python, psycopg2 추가)
├── requirements.txt
├── .env                        # 공통 환경변수 (Git 제외)
├── .env.dev                    # dev 환경 차이 (Git 제외)
├── .env.prod                   # prod 환경 차이 (Git 제외, 운영시 사용)
├── .gitignore
├── .dockerignore
├── README.md
├── config/
│   └── init.sql                # airflow_db 생성
├── dags/
│   └── kis_current_price_to_postgres.py    # KIS API → PostgreSQL DAG
├── app/
│   └── estock/                 # 비즈니스 로직 (DAG 에서 import)
│       ├── clients/
│       │   └── kis_client.py           # KIS API 호출 + 토큰 캐싱
│       ├── repositories/
│       │   └── stock_price_repository.py   # PostgreSQL 적재
│       └── services/
│           └── stock_price_service.py      # client + repository 조합
├── producer/                   # Kafka producer 스크립트
│   └── test_producer.py
└── plugins/                    # Airflow 플러그인 (현재 비어있음)
```

## 4. 환경 분리 전략

### 파일 구성

`.env` 에 **공통 변수**, `.env.dev` / `.env.prod` 에 **환경별 차이만** 작성.
실행 시 두 파일을 같이 로드하여 dev/prod 가 자동 분기.

```bash
# 공통 변수 (모든 환경에서 동일)
.env:
  POSTGRES_USER=estock
  AIRFLOW_UID=50000
  KAFKA_ADVERTISED_HOST=localhost
  *_BIND_HOST=127.0.0.1   # 외부 노출 차단
```

```bash
# dev: 모의투자 + 1xxxx 포트
.env.dev:
  COMPOSE_PROJECT_NAME=estock-dev
  POSTGRES_PASSWORD=estock_dev_pw
  POSTGRES_DB=estock_dev
  KAFKA_HOST_PORT=19092
  AIRFLOW_WEBSERVER_HOST_PORT=18080
  KIS_BASE_URL=https://openapivts.koreainvestment.com:29443
  AIRFLOW_FERNET_KEY=<생성한 키>
  AIRFLOW_WEBSERVER_SECRET_KEY=<생성한 키>
  KIS_APP_KEY=<KIS 발급 키>
  KIS_APP_SECRET=<KIS 발급 시크릿>
```

```bash
# prod: 실전 서버 + 2xxxx 포트 (포트 충돌 방지)
.env.prod:
  COMPOSE_PROJECT_NAME=estock-prod
  POSTGRES_DB=estock_prod
  KAFKA_HOST_PORT=29092
  AIRFLOW_WEBSERVER_HOST_PORT=28080
  KIS_BASE_URL=https://openapi.koreainvestment.com:9443
```

### 키 생성 방법

```bash
# Airflow SECRET_KEY (세션 유지용)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Airflow FERNET_KEY (Variable/Connection 암호화용)
docker run --rm apache/airflow:2.10.0-python3.11 \
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 5. 실행 방법

### 5-1. 첫 실행 (인프라 기동)

```bash
# .env 파일 준비 (.env.example 참고하여 작성)

# 인프라 + Airflow 메타DB 초기화 + 서비스 기동 (한 번에)
docker compose --env-file .env --env-file .env.dev up -d

# 1~2분 후 상태 확인 (kafka healthy + airflow-init 완료까지)
docker compose --env-file .env --env-file .env.dev ps
```

기대 결과:
```
estock-dev-postgres            Up (healthy)
estock-dev-zookeeper           Up
estock-dev-kafka-1             Up (healthy)
estock-dev-kafka-ui            Up
estock-dev-airflow-init        Exited (0)       ← 정상 종료
estock-dev-airflow-webserver   Up
estock-dev-airflow-scheduler   Up
```

### 5-2. 접속

| 서비스      | URL                              | 계정              |
| ---------- | -------------------------------- | ---------------- |
| Airflow UI | http://localhost:18080           | airflow/airflow  |
| Kafka UI   | http://localhost:18088           | -                |
| PostgreSQL | localhost:15439                  | estock/estock_dev_pw |

### 5-3. KIS API DAG 실행

Airflow UI 접속 → `kis_current_price_to_postgres` DAG → 토글 ON → Trigger

검증 (DB 에 데이터 적재 확인):
```bash
docker compose --env-file .env --env-file .env.dev exec postgres \
  psql -U estock -d estock_dev \
  -c "SELECT stock_code, stock_name, current_price, collected_at FROM kis_domestic_stock_price ORDER BY collected_at DESC LIMIT 5;"
```

### 5-4. Kafka Producer 테스트

컨테이너 안에서 실행 (호스트 환경 더럽히지 않음):

```bash
docker compose --env-file .env --env-file .env.dev exec airflow-scheduler \
  python /opt/airflow/producers/test_producer.py
```

기대 출력:
```
[producer] connected to kafka-1:29092
[producer] sending to topic: test-stock-prices
  [1] 삼성전자: 74,832원 (vol=53,210)
  [2] SK하이닉스: 178,440원 (vol=78,901)
  ...
```

Ctrl+C 로 종료. 검증:
```bash
# 토픽 확인
docker compose --env-file .env --env-file .env.dev exec kafka-1 \
  kafka-topics --bootstrap-server kafka-1:29092 --list

# 메시지 직접 읽기
docker compose --env-file .env --env-file .env.dev exec kafka-1 \
  kafka-console-consumer --bootstrap-server kafka-1:29092 \
  --topic test-stock-prices --from-beginning --max-messages 5
```

또는 Kafka UI 에서 시각적으로:
http://localhost:18088 → estock-cluster → Topics → test-stock-prices → Messages

### 5-5. 종료

```bash
# 컨테이너만 정지 (데이터 유지)
docker compose --env-file .env --env-file .env.dev down

# 데이터까지 완전 삭제 (DB 초기화)
docker compose --env-file .env --env-file .env.dev down -v
```

## 6. 핵심 설계 결정

### 왜 단일 Kafka 브로커인가
학습용. 운영급 확장 시 브로커 3 개로 늘리고 `replication_factor=3`,
`min.insync.replicas=2` 로 상향. Confluent 공식 권장도 3 의 정족수(quorum) 패턴.

### 왜 호스트 포트가 19092 / 컨테이너 내부는 29092 인가
Kafka 의 dual-listener 패턴:
- **외부 (호스트)**: `localhost:19092` → 도커가 9092 로 포워딩
- **내부 (컨테이너)**: `kafka-1:29092` 직접 연결

producer/consumer 가 어디서 실행되느냐에 따라 다른 주소 사용:
- 호스트에서: `localhost:19092`
- 컨테이너 안에서 (airflow-scheduler 등): `kafka-1:29092`

### 왜 plugins 가 아닌 app 폴더인가
Airflow 의 `plugins/` 는 본래 `AirflowPlugin` 클래스 등록용. 일반 비즈니스
로직 패키지는 `app/` 같은 별도 폴더 + `PYTHONPATH` 설정이 권장 패턴
(Airflow 2.x 공식 가이드).

### 왜 AIRFLOW_UID=50000 인가
Airflow 도커 이미지 내부에 `airflow` 사용자(UID 50000) 가 등록되어 있음.
호스트 UID(보통 1000) 로 컨테이너를 띄우면 `getuser()` 가 사용자명을 못 찾아
Airflow 가 거부. 호스트 폴더 소유자를 50000:0 으로 맞춰서 해결.

```bash
sudo chown -R 50000:0 logs/ dags/ plugins/ app/ producer/
sudo chmod -R g+rwX logs/ dags/ plugins/ app/ producer/
```

호스트 사용자(group 0=root) 도 권한 갖도록 `g+rwX` 부여.

## 7. 학습 진행 단계

| 단계 | 학습 목표                                                                | 상태 |
| --- | ----------------------------------------------------------------------- | ---- |
| 1   | 인프라 구축 (Kafka + Airflow + PostgreSQL) docker-compose 화             | ✅   |
| 2   | dev/prod 환경 분리, FERNET_KEY 등 보안 설정                                | ✅   |
| 3   | KIS API DAG: 한국투자증권 현재가 → PostgreSQL 적재 (PythonOperator)        | ✅   |
| 4   | Kafka Producer 첫 실행: mock 데이터 → 토픽 → Kafka UI 검증                 | ✅   |
| 5   | Kafka Consumer DAG: 토픽 → PostgreSQL 적재 (auto_commit=False)            | ⬜   |
| 6   | KIS Producer: 실 시세를 Kafka 토픽으로 발행 (별도 producer 서비스로 분리)   | ⬜   |
| 7   | 변환 파이프라인: raw → cleaned → mart 3단 구조 (dbt 도입 검토)               | ⬜   |
| 8   | LLM 연동: mart 데이터를 컨텍스트로 LLM 호출, 응답을 Kafka 로 스트림           | ⬜   |
| 9   | 벡터 검색: pgvector 도입 → 뉴스/공시 임베딩 → RAG 파이프라인                | ⬜   |

## 8. 거쳐온 트러블슈팅 기록

학습 과정에서 부딪힌 주요 함정과 해결 방법.

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `airflow-init` race condition | webserver/scheduler 가 init 보다 먼저 시작 | `service_completed_successfully` 의존성 추가 |
| `Permission denied: /opt/airflow/logs/...` | 호스트 폴더 UID 1000, 컨테이너 UID 50000 불일치 | `sudo chown -R 50000:0` + `chmod g+rwX` |
| `The user has no username` | 컨테이너 내 `/etc/passwd` 에 UID 1000 없음 | UID 1000 으로 가지 말고 50000 으로 통일 |
| `ModuleNotFoundError: No module named 'estock'` | docker-compose 에 `app/` 마운트 누락 | `volumes:` 에 `./app:/opt/airflow/app` 추가 |
| `connect to stock_db failed` | repository 의 fallback DB명이 `stock_db`, 실제는 `estock_dev` | fallback 을 `os.getenv("POSTGRES_DB", "estock_dev")` 로 |
| `SyntaxError: Non-UTF-8 code` | producer 코드가 CP949 인코딩 | `iconv -f CP949 -t UTF-8` 로 변환 |
| `NoBrokersAvailable` (컨테이너 안) | bootstrap_server 가 `localhost:19092` (외부 주소) | 컨테이너 안에서는 `kafka-1:29092` |
| `KIS API 키 노출` | `.env` 가 zip 에 포함되어 외부 공유 | `.gitignore` + zip 시 `-x "*/.env*"` 옵션 |

## 9. 보안 체크리스트

- [x] 모든 포트 `127.0.0.1` 바인딩 (외부 노출 차단)
- [x] `AIRFLOW_FERNET_KEY` 설정 (Variable/Connection 암호화)
- [x] `AIRFLOW_WEBSERVER_SECRET_KEY` 랜덤 생성 (세션 보호)
- [x] `.env*` 파일 `.gitignore` 등록
- [ ] zip 공유 시 `-x "*/.env*"` 옵션 사용 (수동 체크 필요)
- [ ] prod 배포 시 Airflow 기본 계정(`airflow/airflow`) 변경
- [ ] prod 배포 시 PostgreSQL 비밀번호 강력화

## 10. 향후 개선 검토

| 영역 | 현재 | 개선안 |
| --- | --- | --- |
| 명령 단순화 | 매번 `--env-file` 두 개 입력 | Makefile 로 `make dev-up` 형태 |
| Producer 운영 | 학습용 컨테이너 내 수동 실행 | docker-compose 의 별도 producer 서비스로 분리, `restart: unless-stopped` |
| 테스트 | 없음 | `tests/` + pytest + KisClient/Repository 모킹 |
| DB Connection 관리 | psycopg2 직접 연결 | Airflow `PostgresHook` + Connection UI 통합 관리 |
| 토픽 자동 생성 | `KAFKA_AUTO_CREATE_TOPICS_ENABLE: true` | `airflow-init` 에서 명시적 토픽 생성 (파티션/replication 제어) |
| 로깅 | `print()` | `logging.info()` 로 통일 (UI 에서 레벨 필터링 가능) |
