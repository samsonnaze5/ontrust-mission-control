"""
Build per-cmd kafka CSVs from manual analysis of main.go + pipeline package.

Schema: direction,topic,consumer_group
- direction = "in" or "out"
- topic = topic name
- consumer_group = set only for "in" rows; empty for "out" (DLQ/producer)

Cmds with no Kafka usage get an empty file (header only).
"""
import csv
from pathlib import Path

ROOT = Path("/Users/kittiphong/Desktop/codes/claude/ontrust-mission-control/artifacts-infra/entrypoint-kafka")
ROOT.mkdir(parents=True, exist_ok=True)

def DLQ(t): return t + ".dlq"

# Per-cmd kafka data: { (service, cmd): [(direction, topic, cg), ...] }
DATA = {
    # === mt5-processor ===
    ("onetrust-mt5-processor", "mt5-account-balance-snapshot-builder"): [
        ("in", "mt5.account.balance.incoming", "mt5-account-balance-snapshot-builder"),
    ],
    ("onetrust-mt5-processor", "mt5-account-balance-snapshot-sync"): [
        ("in", "mt5-processor.account.balance.snapshot.created", "mt5-account-balance-snapshot-sync"),
    ],
    ("onetrust-mt5-processor", "mt5-deals-in-ingestor"): [
        ("in",  "mt5.deal.in.received",          "mt5-deals-in-ingestor"),
        ("out", DLQ("mt5.deal.in.received"),     ""),
    ],
    ("onetrust-mt5-processor", "mt5-deals-out-ingestor"): [
        ("in",  "mt5.deal.out.received",         "mt5-deals-out-ingestor"),
        ("out", DLQ("mt5.deal.out.received"),    ""),
    ],
    ("onetrust-mt5-processor", "mt5-position-detector"): [
        ("in",  "mt5-processor.deal.out.created",        "mt5-position-detector"),
        ("out", DLQ("mt5-processor.deal.out.created"),   ""),
    ],

    # === financial-service ===
    ("onetrust-financial-service", "consumer-account-event"): [
        ("in",  "account.events",      "financial-account-event-group"),
        ("out", DLQ("account.events"), ""),
    ],
    ("onetrust-financial-service", "consumer-financial-command"): [
        ("in",  "financial.commands",      "financial-command-group"),
        ("out", DLQ("financial.commands"), ""),
    ],
    ("onetrust-financial-service", "consumer-trade-event"): [
        ("in",  "trade.events",      "financial-trade-event-group"),
        ("out", DLQ("trade.events"), ""),
    ],
    ("onetrust-financial-service", "financial-rebate-accrual-builder"): [
        ("in",  "financial.rebate.calculated",      "financial-rebate-accrual-builder"),
        ("out", DLQ("financial.rebate.calculated"), ""),
    ],
    ("onetrust-financial-service", "financial-rebate-calculator"): [
        ("in",  "mt5-processor.deal.out.created",      "financial-rebate-calculator"),
        ("out", DLQ("mt5-processor.deal.out.created"), ""),
    ],
    ("onetrust-financial-service", "financial-rebate-earning-calculator"): [
        # scaffold — no DLQ wrapper
        ("in",  "financial.wallet.transaction.created", "financial-rebate-earning-calculator"),
    ],
    ("onetrust-financial-service", "financial-wallet-transaction-writer"): [
        ("in",  "financial.rebate.settlement.created",      "financial-wallet-transaction-writer"),
        ("out", DLQ("financial.rebate.settlement.created"), ""),
    ],
    ("onetrust-financial-service", "grpc-server"): [],
    ("onetrust-financial-service", "rebate-settlement-scheduler"): [],
    ("onetrust-financial-service", "server"): [],
    ("onetrust-financial-service", "server-worker"): [
        # outbox publisher → Kafka ledger.events
        ("out", "ledger.events", ""),
    ],

    # === archiver ===
    ("onetrust-archiver", "api"): [],
    ("onetrust-archiver", "financial-rebate-accrual-archived"): [
        ("in", "financial.rebate.accrual.created", "financial-rebate-accrual-archived"),
    ],
    ("onetrust-archiver", "financial-rebate-accruals-cleaner"): [
        ("in", "paid.clean", "financial-rebate-accruals-cleaner"),
    ],
    ("onetrust-archiver", "financial-rebate-distribution-archived"): [
        ("in", "financial.rebate.calculated", "financial-rebate-distribution-archived"),
    ],
    ("onetrust-archiver", "financial-rebate-distributions-cleaner"): [
        ("in", "paid.clean", "financial-rebate-distributions-cleaner"),
    ],
    ("onetrust-archiver", "financial-rebate-settlement-archived"): [
        ("in", "financial.rebate.settlement.created", "financial-rebate-settlement-archived"),
    ],
    ("onetrust-archiver", "financial-rebate-settlements-cleaner"): [
        ("in", "paid.clean", "financial-rebate-settlements-cleaner"),
    ],
    ("onetrust-archiver", "financial-wallet-transaction-archived"): [
        ("in", "financial.wallet.transaction.created", "financial-wallet-transaction-archived"),
    ],
    ("onetrust-archiver", "financial-wallet-transactions-cleaner"): [
        ("in", "paid.clean", "financial-wallet-transactions-cleaner"),
    ],
    ("onetrust-archiver", "mt5-account-balance-snapshot-archived"): [
        # scaffold — no DLQ wrapper
        ("in", "mt5-processor.account.balance.snapshot.created", "mt5-account-balance-snapshot-archived"),
    ],
    ("onetrust-archiver", "mt5-account-balance-snapshot-cleaner"): [
        ("in", "mt5.account.balance.snapshot.clean", "mt5-account-balance-snapshot-cleaner"),
    ],
    ("onetrust-archiver", "mt5-account-balance-snapshot-cleanup-watcher"): [],
    ("onetrust-archiver", "mt5-deals-in-archived"): [
        ("in", "mt5-processor.deal.in.created", "mt5-deals-in-archived"),
    ],
    ("onetrust-archiver", "mt5-deals-in-cleaner"): [
        ("in", "paid.clean", "mt5-deals-in-cleaner"),
    ],
    ("onetrust-archiver", "mt5-deals-out-archived"): [
        ("in", "mt5-processor.deal.out.created", "mt5-deals-out-archived"),
    ],
    ("onetrust-archiver", "mt5-deals-out-cleaner"): [
        ("in", "paid.clean", "mt5-deals-out-cleaner"),
    ],
    ("onetrust-archiver", "mt5-position-archived"): [
        ("in", "mt5-processor.position.created", "mt5-position-archived"),
    ],
    ("onetrust-archiver", "mt5-position-cleaner"): [
        ("in", "paid.clean", "mt5-position-cleaner"),
    ],
    ("onetrust-archiver", "rebate-accrual-scheduler"): [],
    ("onetrust-archiver", "rebate-paid-cleanup-watcher"): [],

    # === client-portal-api ===
    ("onetrust-client-portal-api", "server"): [],
    ("onetrust-client-portal-api", "server-admin"): [],
    ("onetrust-client-portal-api", "server-ledger"): [
        # Kafka usage conditional on Service.Outbox.Mode=kafka; defaults: topic=ledger.events, group=ledger-consumer
        ("in", "ledger.events", "ledger-consumer"),
    ],
    ("onetrust-client-portal-api", "server-partner"): [],
    ("onetrust-client-portal-api", "server-swagger"): [],
    ("onetrust-client-portal-api", "server-test"): [],
    ("onetrust-client-portal-api", "server-worker"): [
        # outbox publisher → Kafka if Outbox.Mode=kafka; defaults: topic=ledger.events
        ("out", "ledger.events", ""),
    ],

    # === mt5-proxy-api ===
    ("onetrust-mt5-proxy-api", "server"): [],
}

count_files = 0
count_rows = 0
for (svc, cmd), rows in DATA.items():
    out = ROOT / svc / f"{cmd}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(["direction", "topic", "consumer_group"])
        for r in rows:
            w.writerow(r)
    count_files += 1
    count_rows += len(rows)

print(f"Wrote {count_files} kafka CSVs ({count_rows} total rows)")
print()
# Summary by service
from collections import defaultdict
by_svc = defaultdict(lambda: [0, 0, 0])  # files, rows, has-kafka
for (svc, cmd), rows in DATA.items():
    by_svc[svc][0] += 1
    by_svc[svc][1] += len(rows)
    if rows:
        by_svc[svc][2] += 1
for svc, (n, r, h) in sorted(by_svc.items()):
    print(f"  {svc}: {n} cmds | {h} use Kafka | {r} rows")
