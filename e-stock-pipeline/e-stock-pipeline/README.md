# e-stock-pipeline

주식 데이터와 LLM 응답을 다루는 데이터 파이프라인의 **인프라 골격**.
DAG, 토픽, 테이블 스키마는 학습하며 단계적으로 추가한다.

## 1. 아키텍처 비전

```
   ┌─────────────┐    ┌─────────────┐    ┌────────────────┐    ┌──────────────┐
   │   Airflow   │───▶│    Kafka    │───▶│   PostgreSQL   │───▶│  LLM 컨텍스트  │
   │             │    │             │    │                │    │              │
   │  주기적      │    │  실시간      │    │  raw → cleaned │    │  정제 데이터  │
   │  API 호출    │    │  스트림 버퍼 │    │  → mart 변환    │    │  기반 RAG     │
   │  (KIS,      │    │  + LLM      │    │                │    │              │
   │   pykrx,    │    │  응답 저장   │    │  (data mart /  │    │              │
   │   뉴스 등)   │    │             │    │   warehouse)   │    │              │
   └─────────────┘    └─────────────┘    └────────────────┘    └──────────────┘
```

데이터 흐름 예시:
1. **Airflow (주기 실행)** → 외부 API 호출 → Kafka 토픽으로 적재
2. **Kafka consumer** → Postgres `raw` 테이블에 저장
3. **Airflow (변환)** → `raw` → `cleaned` → `mart` 단계별 변환
4. **LLM 연동** → `mart` 의 정제된 데이터를 컨텍스트로 LLM 호출, 응답을 다시 Kafka 로 스트림 (선택)

## 2. 현재 구성

이 저장소는 **인프라만** 정의되어 있고 비즈니스 로직(DAG, 토픽, 테이블) 은 비어 있다.

| 컴포넌트     | 역할                                                | 포트 (localhost only) |
| ----------- | --------------------------------------------------- | -------------------- |
| Zookeeper   | Kafka 메타데이터 / 리더 선출                          | 12181                |
| Kafka       | 메시지 브로커 (단일 브로커, healthcheck 활성화)        | 19092                |
| Kafka UI    | 토픽 / 메시지 모니터링 (kafbat fork v1.1.0)           | 18088                |
| Postgres    | `stock_db` (적재) + `airflow_db` (메타) 겸용         | 15439                |
| Airflow     | webserver + scheduler (Python 3.11, 2.10.0)         | 18080                |

모든 포트는 `127.0.0.1` 에만 바인딩되어 외부 노출 차단.

## 3. 폴더 구조

```
e-stock-pipeline/
├── docker-compose.yaml      # 인프라 정의
├── Dockerfile               # Airflow 커스텀 이미지 (kafka-python, psycopg2 추가)
├── requirements.txt
├── .env.example             # 복사해서 .env 로 사용
├── .gitignore
├── .dockerignore
├── README.md
├── config/
│   └── init.sql             # airflow_db 만 생성. 분석용 스키마는 직접 추가
├── dags/                    # Airflow DAG 추가 위치 (현재 비어 있음)
├── plugins/                 # Airflow 커스텀 플러그인
└── logs/                    # 런타임 로그 (gitignore)
```

## 4. 실행 방법

```bash
# 1. 환경변수 파일 생성
cp .env.example .env

# 2. SECRET_KEY 를 랜덤 문자열로 교체 (세션 유지에 필수)
python3 -c "import secrets; print(secrets.token_hex(32))"
# 출력값을 .env 의 AIRFLOW_WEBSERVER_SECRET_KEY 에 붙여넣기

# 3. (Linux/Mac) AIRFLOW_UID 를 호스트 사용자로 맞추기 (logs/ 권한 문제 방지)
echo "AIRFLOW_UID=$(id -u)" >> .env

# 4. 인프라 기동 + Airflow 메타DB 초기화 (최초 1회)
docker compose up -d zookeeper kafka-1 kafka-ui postgres
docker compose run --rm airflow-init

# 5. Airflow 기동
docker compose up -d airflow-webserver airflow-scheduler

# 6. 접속
#    Airflow UI : http://localhost:18080  (airflow / airflow)
#    Kafka UI   : http://localhost:18088
#    Postgres   : localhost:15439 (계정은 .env 참조)
```

종료:

```bash
docker compose down              # 컨테이너만 제거 (볼륨 유지)
docker compose down -v           # 볼륨까지 제거 (DB 초기화)
```

## 5. 학습 로드맵

각 단계마다 DAG, 토픽, 테이블을 하나씩 추가하며 점진적으로 확장.

| 단계 | 학습 목표                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------- |
| 1   | **Airflow 기본기**: PythonOperator 로 외부 API (pykrx, KIS, 뉴스) 호출 → 로컬 파일 저장                       |
| 2   | **Kafka 입문**: Producer 작성 → API 응답을 토픽 적재 → Kafka UI 로 메시지 흐름 관찰                          |
| 3   | **Consumer + Postgres**: Kafka 에서 읽어 `raw_*` 테이블에 적재 (`enable_auto_commit=False` 로 정확성 확보)   |
| 4   | **변환 파이프라인**: `raw` → `cleaned` → `mart` 3단 변환. dbt 도입 검토                                       |
| 5   | **LLM 연동**: `mart` 의 정제 데이터를 컨텍스트로 LLM API 호출, 응답을 Kafka 토픽으로 스트림 저장               |
| 6   | **벡터 검색**: pgvector 확장 도입 (또는 Qdrant 별도 컨테이너) → 뉴스/공시 임베딩 → RAG 파이프라인 구성         |
| 7   | **운영급 확장**: Kafka 브로커 1→3, partition 키 설계, exactly-once semantics, 토픽별 retention 정책          |

## 6. 버전 고정 정책

`:latest` 태그는 사용하지 않음. 모든 이미지/패키지는 명시적 버전.

| 컴포넌트         | 고정 버전                              | 선택 근거                                                    |
| --------------- | ------------------------------------ | ----------------------------------------------------------- |
| Confluent CP    | `7.7.1`                              | 7.5 는 standard support 종료(2025-05). 7.7.1 은 ZooKeeper 모드 공식 최소 권장. 8.x 는 ZK 미지원. |
| Kafka UI        | `ghcr.io/kafbat/kafka-ui:v1.1.0`     | 원본 `provectuslabs/kafka-ui` 는 유지보수 중단(CVE-2023-52251 RCE 미패치). kafbat 포크 v1.1.0 (2025-01) 이 검증된 안정 태그. |
| PostgreSQL      | `postgres:15.17-alpine`              | 15 계열 최신 패치 (2026-02), alpine 변종.                       |
| Airflow         | `apache/airflow:2.10.0-python3.11`   | 메이저+마이너+파이썬 버전 모두 고정. constraints 파일과 함께 패키지 버전까지 사실상 고정. |
| kafka-python    | `2.0.2`                              | 마지막으로 폭넓게 검증된 안정 버전.                              |
| psycopg2-binary | `2.9.9`                              | Postgres 15 호환 안정 버전.                                  |

## 7. 적용된 운영 안정성 설정

처음부터 자주 부딪히는 함정들을 미리 막아둔 항목:

- **Kafka healthcheck**: `kafka-topics --list` 로 브로커 ready 확인. kafka-ui 가 healthy 조건 대기.
- **`airflow-init` idempotent**: 사용자 이미 존재해도 init 재실행이 가능 (`|| echo skipping`).
- **Postgres healthcheck**: airflow 가 DB ready 확인 후 기동.
- **AIRFLOW_UID 적용**: 호스트 UID 와 맞춰 `logs/` 권한 충돌 방지.
- **`AIRFLOW__WEBSERVER__SECRET_KEY` 고정**: webserver 재시작 시 세션 유지.
- **Kafka JVM heap 제한**: 512MB 로 제한해 노트북 환경 OOM 방지.
- **`restart: unless-stopped` 전 서비스 적용**: 단발성 크래시 자동 복구.
- **포트 `127.0.0.1` 바인딩**: 외부 네트워크 노출 차단 (카페/회사망 안전).
- **`.dockerignore`**: 빌드 컨텍스트 최소화.

## 8. 트러블슈팅

- **Kafka 연결 실패 (NoBrokersAvailable)**: kafka-1 healthcheck 가 healthy 될 때까지 30~60초 소요. `docker compose ps` 로 STATUS 확인.
- **Airflow init 멈춤**: postgres healthcheck 대기 중일 가능성. `docker compose logs postgres` 확인.
- **DAG 가 webserver UI 에 안 보임**: 파싱 에러 가능. `docker compose logs airflow-scheduler` 확인.
- **`logs/` 디렉터리 권한 에러 (Permission denied)**: `.env` 의 `AIRFLOW_UID` 가 호스트 UID 와 다름. `id -u` 로 확인 후 수정.
- **Postgres 비번 변경 후 재기동 실패**: 볼륨에 이전 비번 남아 있음. `docker compose down -v` 후 재기동.
- **회사 DRM 으로 WSL2/Docker Desktop 차단**: Rancher Desktop 또는 사내 개발 VM 위에서 실행.
