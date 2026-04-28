# Cross-Check Report — Backend Code vs PRD Infrastructure

_Generated: build_cross_check_report.py • Source: 5 backend repos × infra repo `aeternix-crm` (kubeflow/prd)_

This report compares **what the backend code requires** (entrypoints, envs, kafka topics + consumer groups) against **what's actually deployed in PRD K8s + Kafka**. Use it to spot drift, missing envs, name mismatches, and orphans.

## Summary

- **Backend cmds total:** 44
- **Cmds deployed in PRD:** 26 (linked via `k8s-workloads.csv.entrypoint_*`)
- **Workload-cmd pairs analyzed:** 27
- **Env: all required satisfied (no missing):** 15
- **Env: missing some envs in infra:** 12
- **Kafka: clean (topic + CG match):** 0
- **Kafka: at least 1 issue (topic missing / CG mismatch):** 20
- **PRD workloads NOT mapped to a backend cmd:** 35 (Debezium / Python / Jobs / seeders)

## Top Action Items for DevOps

### 🔴 ENV — Required envs missing in PRD ConfigMap/Secret

| Workload | Service | Cmd | Missing envs |
|---|---|---|---|
| financial-rebate-accrual-archived | onetrust-archiver | financial-rebate-accrual-archived | `CLICKHOUSE_IB_DATABASE`, `CLICKHOUSE_IB_ENABLE`, `CLICKHOUSE_IB_HOST`, `CLICKHOUSE_IB_PASSWORD`, `CLICKHOUSE_IB_TLS`, `CLICKHOUSE_IB_USERNAME`, `DATABASE_PORT` |
| financial-rebate-settlement-archived | onetrust-archiver | financial-rebate-settlement-archived | `CLICKHOUSE_IB_DATABASE`, `CLICKHOUSE_IB_ENABLE`, `CLICKHOUSE_IB_HOST`, `CLICKHOUSE_IB_PASSWORD`, `CLICKHOUSE_IB_TLS`, `CLICKHOUSE_IB_USERNAME`, `DATABASE_PORT` |
| financial-wallet-transaction-archived | onetrust-archiver | financial-wallet-transaction-archived | `CLICKHOUSE_IB_DATABASE`, `CLICKHOUSE_IB_ENABLE`, `CLICKHOUSE_IB_HOST`, `CLICKHOUSE_IB_PASSWORD`, `CLICKHOUSE_IB_TLS`, `CLICKHOUSE_IB_USERNAME`, `DATABASE_PORT` |
| aeternix-archiver | onetrust-archiver | mt5-deals-in-archived | `CLICKHOUSE_CLIENT_DATABASE`, `CLICKHOUSE_CLIENT_ENABLE`, `CLICKHOUSE_CLIENT_HOST`, `CLICKHOUSE_CLIENT_PASSWORD`, `CLICKHOUSE_CLIENT_TLS`, `CLICKHOUSE_CLIENT_USERNAME`, `DATABASE_PORT` |
| mt5-position-archiver | onetrust-archiver | mt5-position-archived | `CLICKHOUSE_CLIENT_DATABASE`, `CLICKHOUSE_CLIENT_ENABLE`, `CLICKHOUSE_CLIENT_HOST`, `CLICKHOUSE_CLIENT_PASSWORD`, `CLICKHOUSE_CLIENT_TLS`, `CLICKHOUSE_CLIENT_USERNAME`, `DATABASE_PORT` |
| aeternix-be-admin | onetrust-client-portal-api | server-admin | `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, `FRONTEND_BASE_URL`, `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `JWT_SECRET`, `MT5_PROXY_DEMO_API_KEY`, `MT5_PROXY_DEMO_BASE_URL`, `MT5_PROXY_LIVE_API_KEY`, `MT5_PROXY_LIVE_BASE_URL`, `PSP_HAPPYPAY_API_KEY`, `PSP_HAPPYPAY_ENABLE`, `PSP_MOCK`, `PSP_ONE_TWO_PAY_API_KEY`, `PSP_ONE_TWO_PAY_BASE_URL`, `PSP_ONE_TWO_PAY_ENABLE`, `PSP_ONE_TWO_PAY_PARTNER_CODE`, `SERVICE_ADMIN_AUTH_ACCESS_TOKEN_TTL`, `SERVICE_ADMIN_AUTH_REFRESH_TOKEN_TTL` |
| aeternix-be-partner | onetrust-client-portal-api | server-partner | `FRONTEND_BASE_URL`, `FRONTEND_REGISTER_PATH`, `JWT_SECRET`, `MT5_PROXY_DEMO_API_KEY`, `MT5_PROXY_DEMO_BASE_URL`, `MT5_PROXY_LIVE_API_KEY`, `MT5_PROXY_LIVE_BASE_URL`, `PSP_HAPPYPAY_API_KEY`, `PSP_HAPPYPAY_ENABLE`, `PSP_MOCK`, `PSP_ONE_TWO_PAY_API_KEY`, `PSP_ONE_TWO_PAY_BASE_URL`, `PSP_ONE_TWO_PAY_ENABLE`, `PSP_ONE_TWO_PAY_PARTNER_CODE` |
| aeternix-be | onetrust-client-portal-api | server | `AWS_ACCESS_KEY`, `AWS_S3_BUCKET_NAME`, `AWS_S3_BUCKET_PATH`, `AWS_S3_REGION`, `AWS_SECRET_KEY`, `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, `FRONTEND_BASE_URL`, `FRONTEND_REGISTER_PATH`, `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `JWT_SECRET`, `MT5_PROXY_DEMO_API_KEY`, `MT5_PROXY_DEMO_BASE_URL`, `MT5_PROXY_LIVE_API_KEY`, `MT5_PROXY_LIVE_BASE_URL`, `PSP_HAPPYPAY_API_KEY`, `PSP_HAPPYPAY_ENABLE`, `PSP_MOCK`, `PSP_ONE_TWO_PAY_API_KEY`, `PSP_ONE_TWO_PAY_BASE_URL`, `PSP_ONE_TWO_PAY_ENABLE`, `PSP_ONE_TWO_PAY_PARTNER_CODE`, `SERVICE_AUTH_ACCESS_TOKEN_TTL`, `SERVICE_AUTH_REFRESH_TOKEN_TTL`, `SERVICE_DEPOSIT_IDEMPOTENCY_TTL`, `SERVICE_DEPOSIT_TRANSACTION_EXPIRY_DURATION`, `STORAGE_DRIVER`, `STORAGE_PRESIGNED_URL_EXPIRATION`, `STORAGE_TIMEOUT` |
| financial-rebate-calculator | onetrust-financial-service | financial-rebate-calculator | `DATABASE_PORT`, `DATABASE_TRADING_OUT_DATABASE`, `DATABASE_TRADING_OUT_HOST`, `DATABASE_TRADING_OUT_PASSWORD`, `DATABASE_TRADING_OUT_PORT`, `DATABASE_TRADING_OUT_USERNAME` |
| mt5-deals-in-ingestor | onetrust-mt5-processor | mt5-deals-in-ingestor | `DATABASE_PORT` |
| mt5-deals-out-ingestor | onetrust-mt5-processor | mt5-deals-out-ingestor | `DATABASE_PORT` |
| aeternix-mt5-proxy | onetrust-mt5-proxy-api | server | `MT5_API_KEY`, `MT5_BASE_URL`, `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_REQUEST_TIMEOUT`, `MT5_TLS_INSECURE`, `MT5_VERSION`, `PORT`, `STAGE` |

### 🔴 KAFKA — Topic / Consumer-Group mismatches

| Type | Workload | Service / Cmd | Direction | Detail |
|---|---|---|---|---|
| topic_missing_in_kafka_topics | financial-rebate-accrual-archived | onetrust-archiver / financial-rebate-accrual-archived | in | financial.rebate.accrual.created |
| topic_missing_in_workload | financial-rebate-accrual-archived | onetrust-archiver / financial-rebate-accrual-archived | in | financial.rebate.accrual.created |
| topic_missing_in_kafka_topics | financial-rebate-accruals-cleaner | onetrust-archiver / financial-rebate-accruals-cleaner | in | paid.clean |
| topic_missing_in_workload | financial-rebate-accruals-cleaner | onetrust-archiver / financial-rebate-accruals-cleaner | in | paid.clean |
| topic_missing_in_kafka_topics | financial-rebate-settlement-archived | onetrust-archiver / financial-rebate-settlement-archived | in | financial.rebate.settlement.created |
| topic_missing_in_workload | financial-rebate-settlement-archived | onetrust-archiver / financial-rebate-settlement-archived | in | financial.rebate.settlement.created |
| topic_missing_in_kafka_topics | financial-rebate-settlements-cleaner | onetrust-archiver / financial-rebate-settlements-cleaner | in | paid.clean |
| topic_missing_in_workload | financial-rebate-settlements-cleaner | onetrust-archiver / financial-rebate-settlements-cleaner | in | paid.clean |
| topic_missing_in_kafka_topics | financial-wallet-transaction-archived | onetrust-archiver / financial-wallet-transaction-archived | in | financial.wallet.transaction.created |
| topic_missing_in_workload | financial-wallet-transaction-archived | onetrust-archiver / financial-wallet-transaction-archived | in | financial.wallet.transaction.created |
| topic_missing_in_kafka_topics | mt5-account-balance-snapshot-archived | onetrust-archiver / mt5-account-balance-snapshot-archived | in | mt5-processor.account.balance.snapshot.created |
| topic_missing_in_workload | mt5-account-balance-snapshot-archived | onetrust-archiver / mt5-account-balance-snapshot-archived | in | mt5-processor.account.balance.snapshot.created |
| cg_mismatch | mt5-account-balance-snapshot-archived | onetrust-archiver / mt5-account-balance-snapshot-archived | in | code=mt5-account-balance-snapshot-archived infra=mt5-balance-snapshot-archived |
| topic_missing_in_kafka_topics | aeternix-archiver | onetrust-archiver / mt5-deals-in-archived | in | mt5-processor.deal.in.created |
| topic_missing_in_workload | aeternix-archiver | onetrust-archiver / mt5-deals-in-archived | in | mt5-processor.deal.in.created |
| cg_mismatch | aeternix-archiver | onetrust-archiver / mt5-deals-in-archived | in | code=mt5-deals-in-archived infra=(via archiver-config) |
| topic_missing_in_kafka_topics | mt5-deals-in-cleaner | onetrust-archiver / mt5-deals-in-cleaner | in | paid.clean |
| topic_missing_in_workload | mt5-deals-in-cleaner | onetrust-archiver / mt5-deals-in-cleaner | in | paid.clean |
| topic_missing_in_kafka_topics | mt5-deals-out-cleaner | onetrust-archiver / mt5-deals-out-cleaner | in | paid.clean |
| topic_missing_in_workload | mt5-deals-out-cleaner | onetrust-archiver / mt5-deals-out-cleaner | in | paid.clean |
| topic_missing_in_kafka_topics | mt5-position-archiver | onetrust-archiver / mt5-position-archived | in | mt5-processor.position.created |
| topic_missing_in_workload | mt5-position-archiver | onetrust-archiver / mt5-position-archived | in | mt5-processor.position.created |
| topic_missing_in_kafka_topics | mt5-position-cleaner | onetrust-archiver / mt5-position-cleaner | in | paid.clean |
| topic_missing_in_workload | mt5-position-cleaner | onetrust-archiver / mt5-position-cleaner | in | paid.clean |
| topic_missing_in_kafka_topics | aeternix-finance-service | onetrust-financial-service / financial-rebate-accrual-builder | in | financial.rebate.calculated |
| topic_missing_in_workload | aeternix-finance-service | onetrust-financial-service / financial-rebate-accrual-builder | in | financial.rebate.calculated |
| cg_mismatch | aeternix-finance-service | onetrust-financial-service / financial-rebate-accrual-builder | in | code=financial-rebate-accrual-builder infra=(via finance-service-config) |
| topic_missing_in_kafka_topics | aeternix-finance-service | onetrust-financial-service / financial-rebate-accrual-builder | out | financial.rebate.calculated.dlq |
| topic_missing_in_kafka_topics | financial-rebate-accrual-builder | onetrust-financial-service / financial-rebate-accrual-builder | in | financial.rebate.calculated |
| topic_missing_in_workload | financial-rebate-accrual-builder | onetrust-financial-service / financial-rebate-accrual-builder | in | financial.rebate.calculated |
| topic_missing_in_kafka_topics | financial-rebate-accrual-builder | onetrust-financial-service / financial-rebate-accrual-builder | out | financial.rebate.calculated.dlq |
| topic_missing_in_kafka_topics | financial-rebate-calculator | onetrust-financial-service / financial-rebate-calculator | in | mt5-processor.deal.out.created |
| topic_missing_in_workload | financial-rebate-calculator | onetrust-financial-service / financial-rebate-calculator | in | mt5-processor.deal.out.created |
| topic_missing_in_kafka_topics | financial-rebate-calculator | onetrust-financial-service / financial-rebate-calculator | out | mt5-processor.deal.out.created.dlq |
| topic_missing_in_kafka_topics | financial-wallet-transaction-writer | onetrust-financial-service / financial-wallet-transaction-writer | in | financial.rebate.settlement.created |
| topic_missing_in_workload | financial-wallet-transaction-writer | onetrust-financial-service / financial-wallet-transaction-writer | in | financial.rebate.settlement.created |
| topic_missing_in_kafka_topics | financial-wallet-transaction-writer | onetrust-financial-service / financial-wallet-transaction-writer | out | financial.rebate.settlement.created.dlq |
| topic_missing_in_kafka_topics | mt5-account-balance-snapshot-builder | onetrust-mt5-processor / mt5-account-balance-snapshot-builder | in | mt5.account.balance.incoming |
| topic_missing_in_workload | mt5-account-balance-snapshot-builder | onetrust-mt5-processor / mt5-account-balance-snapshot-builder | in | mt5.account.balance.incoming |
| cg_mismatch | mt5-account-balance-snapshot-builder | onetrust-mt5-processor / mt5-account-balance-snapshot-builder | in | code=mt5-account-balance-snapshot-builder infra=mt5-balance-snapshot-builder |
| topic_missing_in_kafka_topics | mt5-account-balance-snapshot-sync | onetrust-mt5-processor / mt5-account-balance-snapshot-sync | in | mt5-processor.account.balance.snapshot.created |
| topic_missing_in_workload | mt5-account-balance-snapshot-sync | onetrust-mt5-processor / mt5-account-balance-snapshot-sync | in | mt5-processor.account.balance.snapshot.created |
| cg_mismatch | mt5-account-balance-snapshot-sync | onetrust-mt5-processor / mt5-account-balance-snapshot-sync | in | code=mt5-account-balance-snapshot-sync infra=mt5-balance-snapshot-sync |
| topic_missing_in_workload | mt5-deals-in-ingestor | onetrust-mt5-processor / mt5-deals-in-ingestor | in | mt5.deal.in.received |
| cg_mismatch | mt5-deals-in-ingestor | onetrust-mt5-processor / mt5-deals-in-ingestor | in | code=mt5-deals-in-ingestor infra=mt5proc-deal-in |
| topic_missing_in_kafka_topics | mt5-deals-in-ingestor | onetrust-mt5-processor / mt5-deals-in-ingestor | out | mt5.deal.in.received.dlq |
| topic_missing_in_workload | mt5-deals-out-ingestor | onetrust-mt5-processor / mt5-deals-out-ingestor | in | mt5.deal.out.received |
| cg_mismatch | mt5-deals-out-ingestor | onetrust-mt5-processor / mt5-deals-out-ingestor | in | code=mt5-deals-out-ingestor infra=mt5proc-deal-out |
| topic_missing_in_kafka_topics | mt5-deals-out-ingestor | onetrust-mt5-processor / mt5-deals-out-ingestor | out | mt5.deal.out.received.dlq |
| topic_missing_in_kafka_topics | position-completion-detector | onetrust-mt5-processor / mt5-position-detector | in | mt5-processor.deal.out.created |
| topic_missing_in_workload | position-completion-detector | onetrust-mt5-processor / mt5-position-detector | in | mt5-processor.deal.out.created |
| topic_missing_in_kafka_topics | position-completion-detector | onetrust-mt5-processor / mt5-position-detector | out | mt5-processor.deal.out.created.dlq |

## Per-cmd Detail

Click through to inspect each deployed cmd's env + kafka comparison. Cmds NOT deployed in PRD are listed at the bottom.

### `onetrust-archiver`

#### `api` — _NOT deployed in PRD_

- Code-required envs: 3

#### `financial-rebate-accrual-archived` → workload `financial-rebate-accrual-archived`

**Env** — code requires 13 • infra provides 12 • 🔴 7 missing

- 🔴 Missing in infra: `CLICKHOUSE_IB_DATABASE`, `CLICKHOUSE_IB_ENABLE`, `CLICKHOUSE_IB_HOST`, `CLICKHOUSE_IB_PASSWORD`, `CLICKHOUSE_IB_TLS`, `CLICKHOUSE_IB_USERNAME`, `DATABASE_PORT`

- 🟡 Set in infra but unused by code (still in `envs.csv`): `CLICKHOUSE_DATABASE`, `CLICKHOUSE_PASSWORD`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `CLICKHOUSE_ENDPOINT`, `CLICKHOUSE_USER`, `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `financial.rebate.accrual.created` → CG `financial-rebate-accrual-archived` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

#### `financial-rebate-accruals-cleaner` → workload `financial-rebate-accruals-cleaner`

**Env** — code requires 8 • infra provides 15 • ✅ all satisfied

- 🟡 Set in infra but unused by code (still in `envs.csv`): `DATABASE_DATABASE`, `DATABASE_PASSWORD`, `DATABASE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_FINANCIAL_SSLMODE`, `DATABASE_SSLMODE`, `METRICS_PORT`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `paid.clean` → CG `financial-rebate-accruals-cleaner` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

#### `financial-rebate-distribution-archived` — _NOT deployed in PRD_

- Code-required envs: 13
- Code Kafka: in=[financial.rebate.calculated] out=[—]

#### `financial-rebate-distributions-cleaner` — _NOT deployed in PRD_

- Code-required envs: 8
- Code Kafka: in=[paid.clean] out=[—]

#### `financial-rebate-settlement-archived` → workload `financial-rebate-settlement-archived`

**Env** — code requires 13 • infra provides 12 • 🔴 7 missing

- 🔴 Missing in infra: `CLICKHOUSE_IB_DATABASE`, `CLICKHOUSE_IB_ENABLE`, `CLICKHOUSE_IB_HOST`, `CLICKHOUSE_IB_PASSWORD`, `CLICKHOUSE_IB_TLS`, `CLICKHOUSE_IB_USERNAME`, `DATABASE_PORT`

- 🟡 Set in infra but unused by code (still in `envs.csv`): `CLICKHOUSE_DATABASE`, `CLICKHOUSE_PASSWORD`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `CLICKHOUSE_ENDPOINT`, `CLICKHOUSE_USER`, `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `financial.rebate.settlement.created` → CG `financial-rebate-settlement-archived` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

#### `financial-rebate-settlements-cleaner` → workload `financial-rebate-settlements-cleaner`

**Env** — code requires 8 • infra provides 14 • ✅ all satisfied

- 🟡 Set in infra but unused by code (still in `envs.csv`): `DATABASE_DATABASE`, `DATABASE_PASSWORD`, `DATABASE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_FINANCIAL_SSLMODE`, `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `paid.clean` → CG `financial-rebate-settlements-cleaner` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

#### `financial-wallet-transaction-archived` → workload `financial-wallet-transaction-archived`

**Env** — code requires 13 • infra provides 12 • 🔴 7 missing

- 🔴 Missing in infra: `CLICKHOUSE_IB_DATABASE`, `CLICKHOUSE_IB_ENABLE`, `CLICKHOUSE_IB_HOST`, `CLICKHOUSE_IB_PASSWORD`, `CLICKHOUSE_IB_TLS`, `CLICKHOUSE_IB_USERNAME`, `DATABASE_PORT`

- 🟡 Set in infra but unused by code (still in `envs.csv`): `CLICKHOUSE_DATABASE`, `CLICKHOUSE_PASSWORD`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `CLICKHOUSE_ENDPOINT`, `CLICKHOUSE_USER`, `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `financial.wallet.transaction.created` → CG `financial-wallet-transaction-archived` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

#### `financial-wallet-transactions-cleaner` — _NOT deployed in PRD_

- Code-required envs: 8
- Code Kafka: in=[paid.clean] out=[—]

#### `mt5-account-balance-snapshot-archived` → workload `mt5-account-balance-snapshot-archived`

**Env** — code requires 3 • infra provides 14 • ✅ all satisfied

- 🟡 Set in infra but unused by code (still in `envs.csv`): `CLICKHOUSE_DATABASE`, `CLICKHOUSE_ENABLE`, `CLICKHOUSE_HOST`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_USERNAME`, `DATABASE_DATABASE`, `DATABASE_PASSWORD`, `DATABASE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `METRICS_PORT`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `mt5-processor.account.balance.snapshot.created` → CG `mt5-account-balance-snapshot-archived` — 🔴 topic NOT in `kafka-topics.csv` • 🔴 CG mismatch (code=`mt5-account-balance-snapshot-archived` vs infra=`mt5-balance-snapshot-archived`)

#### `mt5-account-balance-snapshot-cleaner` — _NOT deployed in PRD_

- Code-required envs: 8
- Code Kafka: in=[mt5.account.balance.snapshot.clean] out=[—]

#### `mt5-account-balance-snapshot-cleanup-watcher` — _NOT deployed in PRD_

- Code-required envs: 3

#### `mt5-deals-in-archived` → workload `aeternix-archiver`

**Env** — code requires 13 • infra provides 9 • 🔴 7 missing

- 🔴 Missing in infra: `CLICKHOUSE_CLIENT_DATABASE`, `CLICKHOUSE_CLIENT_ENABLE`, `CLICKHOUSE_CLIENT_HOST`, `CLICKHOUSE_CLIENT_PASSWORD`, `CLICKHOUSE_CLIENT_TLS`, `CLICKHOUSE_CLIENT_USERNAME`, `DATABASE_PORT`

- 🟡 Set in infra but unused by code (still in `envs.csv`): `CLICKHOUSE_ENABLE`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `mt5-processor.deal.in.created` → CG `mt5-deals-in-archived` — 🔴 topic NOT in `kafka-topics.csv` • 🔴 CG mismatch (code=`mt5-deals-in-archived` vs infra=`(via archiver-config)`)

#### `mt5-deals-in-cleaner` → workload `mt5-deals-in-cleaner`

**Env** — code requires 8 • infra provides 26 • ✅ all satisfied

- 🟡 Set in infra but unused by code (still in `envs.csv`): `DATABASE_DATABASE`, `DATABASE_PASSWORD`, `DATABASE_POSITION_COMPLETE_DATABASE`, `DATABASE_POSITION_COMPLETE_HOST`, `DATABASE_POSITION_COMPLETE_PASSWORD`, `DATABASE_POSITION_COMPLETE_PORT`, `DATABASE_POSITION_COMPLETE_USERNAME`, `DATABASE_TRADING_OUT_DATABASE`, `DATABASE_TRADING_OUT_HOST`, `DATABASE_TRADING_OUT_PASSWORD`, `DATABASE_TRADING_OUT_PORT`, `DATABASE_TRADING_OUT_USERNAME`, `DATABASE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_POSITION_COMPLETE_SSLMODE`, `DATABASE_SSLMODE`, `DATABASE_TRADING_IN_SSLMODE`, `DATABASE_TRADING_OUT_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `paid.clean` → CG `mt5-deals-in-cleaner` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

#### `mt5-deals-out-archived` — _NOT deployed in PRD_

- Code-required envs: 13
- Code Kafka: in=[mt5-processor.deal.out.created] out=[—]

#### `mt5-deals-out-cleaner` → workload `mt5-deals-out-cleaner`

**Env** — code requires 8 • infra provides 14 • ✅ all satisfied

- 🟡 Set in infra but unused by code (still in `envs.csv`): `DATABASE_DATABASE`, `DATABASE_PASSWORD`, `DATABASE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `DATABASE_TRADING_OUT_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `paid.clean` → CG `mt5-deals-out-cleaner` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

#### `mt5-position-archived` → workload `mt5-position-archiver`

**Env** — code requires 13 • infra provides 13 • 🔴 7 missing

- 🔴 Missing in infra: `CLICKHOUSE_CLIENT_DATABASE`, `CLICKHOUSE_CLIENT_ENABLE`, `CLICKHOUSE_CLIENT_HOST`, `CLICKHOUSE_CLIENT_PASSWORD`, `CLICKHOUSE_CLIENT_TLS`, `CLICKHOUSE_CLIENT_USERNAME`, `DATABASE_PORT`

- 🟡 Set in infra but unused by code (still in `envs.csv`): `CLICKHOUSE_DATABASE`, `CLICKHOUSE_ENABLE`, `CLICKHOUSE_HOST`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `mt5-processor.position.created` → CG `mt5-position-archived` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

#### `mt5-position-cleaner` → workload `mt5-position-cleaner`

**Env** — code requires 8 • infra provides 14 • ✅ all satisfied

- 🟡 Set in infra but unused by code (still in `envs.csv`): `DATABASE_DATABASE`, `DATABASE_PASSWORD`, `DATABASE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_POSITION_COMPLETE_SSLMODE`, `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `paid.clean` → CG `mt5-position-cleaner` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

#### `rebate-accrual-scheduler` → workload `rebate-accrual-scheduler`

**Env** — code requires 3 • infra provides 13 • ✅ all satisfied

- 🟡 Set in infra but unused by code (still in `envs.csv`): `DATABASE_DATABASE`, `DATABASE_FINANCIAL_DATABASE`, `DATABASE_FINANCIAL_HOST`, `DATABASE_FINANCIAL_PASSWORD`, `DATABASE_FINANCIAL_PORT`, `DATABASE_FINANCIAL_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka** — no kafka usage in this cmd

#### `rebate-paid-cleanup-watcher` → workload `rebate-paid-cleanup-watcher`

**Env** — code requires 3 • infra provides 24 • ✅ all satisfied

- 🟡 Set in infra but unused by code (still in `envs.csv`): `CLICKHOUSE_DATABASE`, `CLICKHOUSE_ENABLE`, `CLICKHOUSE_HOST`, `CLICKHOUSE_IB_DATABASE`, `CLICKHOUSE_IB_HOST`, `CLICKHOUSE_IB_PASSWORD`, `CLICKHOUSE_IB_USERNAME`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_USERNAME`, `DATABASE_DATABASE`, `DATABASE_PASSWORD`, `DATABASE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_FINANCIAL_REPLICA_DATABASE`, `DATABASE_FINANCIAL_REPLICA_HOST`, `DATABASE_FINANCIAL_REPLICA_PASSWORD`, `DATABASE_FINANCIAL_REPLICA_PORT`, `DATABASE_FINANCIAL_REPLICA_SSLMODE`, `DATABASE_FINANCIAL_REPLICA_USERNAME`, `DATABASE_SSLMODE`, `METRICS_PORT`, `POD_NAME`

**Kafka** — no kafka usage in this cmd

### `onetrust-client-portal-api`

#### `server` → workload `aeternix-be`

**Env** — code requires 37 • infra provides 13 • 🔴 31 missing

- 🔴 Missing in infra: `AWS_ACCESS_KEY`, `AWS_S3_BUCKET_NAME`, `AWS_S3_BUCKET_PATH`, `AWS_S3_REGION`, `AWS_SECRET_KEY`, `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, `FRONTEND_BASE_URL`, `FRONTEND_REGISTER_PATH`, `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `JWT_SECRET`, `MT5_PROXY_DEMO_API_KEY`, `MT5_PROXY_DEMO_BASE_URL`, `MT5_PROXY_LIVE_API_KEY`, `MT5_PROXY_LIVE_BASE_URL`, `PSP_HAPPYPAY_API_KEY`, `PSP_HAPPYPAY_ENABLE`, `PSP_MOCK`, `PSP_ONE_TWO_PAY_API_KEY`, `PSP_ONE_TWO_PAY_BASE_URL`, `PSP_ONE_TWO_PAY_ENABLE`, `PSP_ONE_TWO_PAY_PARTNER_CODE`, `SERVICE_AUTH_ACCESS_TOKEN_TTL`, `SERVICE_AUTH_REFRESH_TOKEN_TTL`, `SERVICE_DEPOSIT_IDEMPOTENCY_TTL`, `SERVICE_DEPOSIT_TRANSACTION_EXPIRY_DURATION`, `STORAGE_DRIVER`, `STORAGE_PRESIGNED_URL_EXPIRATION`, `STORAGE_TIMEOUT`

- 🟡 Set in infra but NOT in `envs.csv` catalog: `APP_ENV`, `APP_VERSION`, `DATABASE_CONNECT_TIMEOUT`, `DATABASE_SSLMODE`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, `PYROSCOPE_SERVER_ADDRESS`

**Kafka** — no kafka usage in this cmd

#### `server-admin` → workload `aeternix-be-admin`

**Env** — code requires 26 • infra provides 7 • 🔴 20 missing

- 🔴 Missing in infra: `EMAIL_SENDER_EMAIL`, `EMAIL_SENDER_NAME`, `FRONTEND_BASE_URL`, `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `JWT_SECRET`, `MT5_PROXY_DEMO_API_KEY`, `MT5_PROXY_DEMO_BASE_URL`, `MT5_PROXY_LIVE_API_KEY`, `MT5_PROXY_LIVE_BASE_URL`, `PSP_HAPPYPAY_API_KEY`, `PSP_HAPPYPAY_ENABLE`, `PSP_MOCK`, `PSP_ONE_TWO_PAY_API_KEY`, `PSP_ONE_TWO_PAY_BASE_URL`, `PSP_ONE_TWO_PAY_ENABLE`, `PSP_ONE_TWO_PAY_PARTNER_CODE`, `SERVICE_ADMIN_AUTH_ACCESS_TOKEN_TTL`, `SERVICE_ADMIN_AUTH_REFRESH_TOKEN_TTL`

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_CONNECT_TIMEOUT`

**Kafka** — no kafka usage in this cmd

#### `server-ledger` — _NOT deployed in PRD_

- Code-required envs: 19
- Code Kafka: in=[ledger.events] out=[—]

#### `server-partner` → workload `aeternix-be-partner`

**Env** — code requires 20 • infra provides 7 • 🔴 14 missing

- 🔴 Missing in infra: `FRONTEND_BASE_URL`, `FRONTEND_REGISTER_PATH`, `JWT_SECRET`, `MT5_PROXY_DEMO_API_KEY`, `MT5_PROXY_DEMO_BASE_URL`, `MT5_PROXY_LIVE_API_KEY`, `MT5_PROXY_LIVE_BASE_URL`, `PSP_HAPPYPAY_API_KEY`, `PSP_HAPPYPAY_ENABLE`, `PSP_MOCK`, `PSP_ONE_TWO_PAY_API_KEY`, `PSP_ONE_TWO_PAY_BASE_URL`, `PSP_ONE_TWO_PAY_ENABLE`, `PSP_ONE_TWO_PAY_PARTNER_CODE`

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_CONNECT_TIMEOUT`

**Kafka** — no kafka usage in this cmd

#### `server-swagger` — _NOT deployed in PRD_

- Code-required envs: 0

#### `server-test` — _NOT deployed in PRD_

- Code-required envs: 18

#### `server-worker` — _NOT deployed in PRD_

- Code-required envs: 19
- Code Kafka: in=[—] out=[ledger.events]

### `onetrust-financial-service`

#### `consumer-account-event` — _NOT deployed in PRD_

- Code-required envs: 7
- Code Kafka: in=[account.events] out=[account.events.dlq]

#### `consumer-financial-command` — _NOT deployed in PRD_

- Code-required envs: 7
- Code Kafka: in=[financial.commands] out=[financial.commands.dlq]

#### `consumer-trade-event` — _NOT deployed in PRD_

- Code-required envs: 7
- Code Kafka: in=[trade.events] out=[trade.events.dlq]

#### `financial-rebate-accrual-builder` → workload `aeternix-finance-service`

**Env** — code requires 11 • infra provides 13 • ✅ all satisfied

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `financial.rebate.calculated` → CG `financial-rebate-accrual-builder` — 🔴 topic NOT in `kafka-topics.csv` • 🔴 CG mismatch (code=`financial-rebate-accrual-builder` vs infra=`(via finance-service-config)`)

- Outbound (producer):
  - `financial.rebate.calculated.dlq` — 🔴 topic NOT in `kafka-topics.csv` • 🟡 not listed under workload's `topics_out`

#### `financial-rebate-accrual-builder` → workload `financial-rebate-accrual-builder`

**Env** — code requires 11 • infra provides 13 • ✅ all satisfied

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `financial.rebate.calculated` → CG `financial-rebate-accrual-builder` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

- Outbound (producer):
  - `financial.rebate.calculated.dlq` — 🔴 topic NOT in `kafka-topics.csv` • 🟡 not listed under workload's `topics_out`

#### `financial-rebate-calculator` → workload `financial-rebate-calculator`

**Env** — code requires 17 • infra provides 13 • 🔴 6 missing

- 🔴 Missing in infra: `DATABASE_PORT`, `DATABASE_TRADING_OUT_DATABASE`, `DATABASE_TRADING_OUT_HOST`, `DATABASE_TRADING_OUT_PASSWORD`, `DATABASE_TRADING_OUT_PORT`, `DATABASE_TRADING_OUT_USERNAME`

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `mt5-processor.deal.out.created` → CG `financial-rebate-calculator` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

- Outbound (producer):
  - `mt5-processor.deal.out.created.dlq` — 🔴 topic NOT in `kafka-topics.csv` • 🟡 not listed under workload's `topics_out`

#### `financial-rebate-earning-calculator` — _NOT deployed in PRD_

- Code-required envs: 6
- Code Kafka: in=[financial.wallet.transaction.created] out=[—]

#### `financial-wallet-transaction-writer` → workload `financial-wallet-transaction-writer`

**Env** — code requires 11 • infra provides 13 • ✅ all satisfied

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `financial.rebate.settlement.created` → CG `financial-wallet-transaction-writer` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

- Outbound (producer):
  - `financial.rebate.settlement.created.dlq` — 🔴 topic NOT in `kafka-topics.csv` • 🟡 not listed under workload's `topics_out`

#### `grpc-server` — _NOT deployed in PRD_

- Code-required envs: 6

#### `rebate-settlement-scheduler` → workload `rebate-settlement-scheduler`

**Env** — code requires 11 • infra provides 13 • ✅ all satisfied

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka** — no kafka usage in this cmd

#### `server` — _NOT deployed in PRD_

- Code-required envs: 12

#### `server-worker` — _NOT deployed in PRD_

- Code-required envs: 7
- Code Kafka: in=[—] out=[ledger.events]

### `onetrust-mt5-processor`

#### `mt5-account-balance-snapshot-builder` → workload `mt5-account-balance-snapshot-builder`

**Env** — code requires 6 • infra provides 13 • ✅ all satisfied

- 🟡 Set in infra but unused by code (still in `envs.csv`): `DATABASE_TRADING_BALANCE_DATABASE`, `DATABASE_TRADING_BALANCE_HOST`, `DATABASE_TRADING_BALANCE_PASSWORD`, `DATABASE_TRADING_BALANCE_PORT`, `DATABASE_TRADING_BALANCE_USERNAME`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `mt5.account.balance.incoming` → CG `mt5-account-balance-snapshot-builder` — 🔴 topic NOT in `kafka-topics.csv` • 🔴 CG mismatch (code=`mt5-account-balance-snapshot-builder` vs infra=`mt5-balance-snapshot-builder`)

#### `mt5-account-balance-snapshot-sync` → workload `mt5-account-balance-snapshot-sync`

**Env** — code requires 6 • infra provides 13 • ✅ all satisfied

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`, `REDIS_CLUSTER_ENABLED`, `REDIS_ENABLE`, `REDIS_HOST`, `REDIS_PASSWORD`, `REDIS_PORT`

**Kafka**

- Inbound (consumer):
  - `mt5-processor.account.balance.snapshot.created` → CG `mt5-account-balance-snapshot-sync` — 🔴 topic NOT in `kafka-topics.csv` • 🔴 CG mismatch (code=`mt5-account-balance-snapshot-sync` vs infra=`mt5-balance-snapshot-sync`)

#### `mt5-deals-in-ingestor` → workload `mt5-deals-in-ingestor`

**Env** — code requires 12 • infra provides 13 • 🔴 1 missing

- 🔴 Missing in infra: `DATABASE_PORT`

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `mt5.deal.in.received` → CG `mt5-deals-in-ingestor` — 🔴 topic NOT linked to this workload in `kafka-consumers.csv` • 🔴 CG mismatch (code=`mt5-deals-in-ingestor` vs infra=`mt5proc-deal-in`)

- Outbound (producer):
  - `mt5.deal.in.received.dlq` — 🔴 topic NOT in `kafka-topics.csv` • 🟡 not listed under workload's `topics_out`

#### `mt5-deals-out-ingestor` → workload `mt5-deals-out-ingestor`

**Env** — code requires 12 • infra provides 13 • 🔴 1 missing

- 🔴 Missing in infra: `DATABASE_PORT`

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `mt5.deal.out.received` → CG `mt5-deals-out-ingestor` — 🔴 topic NOT linked to this workload in `kafka-consumers.csv` • 🔴 CG mismatch (code=`mt5-deals-out-ingestor` vs infra=`mt5proc-deal-out`)

- Outbound (producer):
  - `mt5.deal.out.received.dlq` — 🔴 topic NOT in `kafka-topics.csv` • 🟡 not listed under workload's `topics_out`

#### `mt5-position-detector` → workload `position-completion-detector`

**Env** — code requires 21 • infra provides 23 • ✅ all satisfied

- 🟡 Set in infra but NOT in `envs.csv` catalog: `DATABASE_SSLMODE`, `POD_NAME`

**Kafka**

- Inbound (consumer):
  - `mt5-processor.deal.out.created` → CG `mt5-position-detector` — 🔴 topic NOT in `kafka-topics.csv` • ✅ CG match

- Outbound (producer):
  - `mt5-processor.deal.out.created.dlq` — 🔴 topic NOT in `kafka-topics.csv` • 🟡 not listed under workload's `topics_out`

### `onetrust-mt5-proxy-api`

#### `server` → workload `aeternix-mt5-proxy`

**Env** — code requires 9 • infra provides 4 • 🔴 9 missing

- 🔴 Missing in infra: `MT5_API_KEY`, `MT5_BASE_URL`, `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_REQUEST_TIMEOUT`, `MT5_TLS_INSECURE`, `MT5_VERSION`, `PORT`, `STAGE`

- 🟡 Set in infra but unused by code (still in `envs.csv`): `KAFKA_BROKERS`
- 🟡 Set in infra but NOT in `envs.csv` catalog: `APP_PORT`, `ENVIRONMENT`, `LOG_LEVEL`

**Kafka** — no kafka usage in this cmd

## Orphan PRD Workloads (no backend-cmd mapping)

These 35 workloads run in PRD but don't link to any of our 5 backend cmds (Python/Debezium/Jobs/seeders). For reference only — no action needed unless one should be migrated to a Go cmd.

```
- aeternix-fe
- aeternix-fe-backoffice
- crm-be
- kafka-stream-processor
- kafka-db-writer
- kafka-pay-processor
- mt5-deals-out-ingestor-py
- mt5-account-sync
- debezium-connect
- debezium-master
- debezium-deal
- debezium-ib
- cdc-metrics-pusher
- kafka-connect-exporter
- mt5-seeder
- debezium-master-setup
- debezium-deal-setup
- debezium-ib-setup
- kafka-topics-setup
- kafka-topic-init
- mt5-seeder-run-002
- mt5-seeder-run-003
- mt5-synthetic-gen
- mt5-synthetic-gen-10m
- mt5-position-complete-backfill
- mt5-position-complete-backfill-v2
- mt5-deals-in-db-copy
- mt5-deals-out-db-copy
- kafka-position-reset
- debezium-balance-snapshot-setup
- debezium-setup
- cdc-perf-test
- ch-kafka-tune
- clone-perf-test
- rds-connection-check
```
