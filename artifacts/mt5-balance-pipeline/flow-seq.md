# Balance Pipeline — Sequence Diagram

ดูคู่กับ [flow.csv](flow.csv) — `[XX]` ในข้อความ = step number ใน flow.csv

```mermaid
sequenceDiagram
    participant MT5 as External MT5 PG
    participant K as Kafka
    participant Builder as snapshot-builder<br/>(mt5-processor)
    participant Sync as snapshot-sync<br/>(mt5-processor)
    participant Arch as snapshot-archived<br/>(archived) [scaffold]
    participant Watcher as cleanup-watcher<br/>(archived) [scaffold]
    participant Cleaner as snapshot-cleaner<br/>(archived)
    participant BalDB as Postgres balance
    participant CH as ClickHouse client

    rect rgba(255,235,205,0.4)
    Note over MT5,BalDB: INGEST
    MT5->>K: [01] debezium → mt5.account.balance.incoming
    K->>Builder: [02] consume
    Builder->>BalDB: [02] INSERT mt5_account_balance_snapshots
    end

    rect rgba(220,235,250,0.4)
    Note over K,CH: PROCESS + ARCHIVE — fan-out 2 จาก snapshot.created
    BalDB->>K: [03] debezium → mt5-processor.account.balance.snapshot.created
    par sync trading equity history
        K->>Sync: [04] consume
        Sync->>BalDB: [04] UPSERT trading equity history (write-only)
    and archive snapshot
        K->>Arch: [05] consume
        Arch->>CH: [05] batch INSERT mt5_account_balance_snapshots
    end
    end

    rect rgba(220,255,220,0.4)
    Note over Watcher,Cleaner: CLEANUP — daily 00:00 UTC
    loop daily 00:00 UTC
        Watcher->>CH: [06] SELECT verify archived
        Watcher->>K: [06] publish mt5.account.balance.snapshot.clean
        K->>Cleaner: [07] consume
        Cleaner->>BalDB: [07] DELETE row by snapshot_id
    end
    end
```

## Legend

- **[scaffold]** — binary มีอยู่แต่ยังเป็น stub (tick log TODO เฉยๆ) ต้อง implement
- สีกล่อง: ส้ม = INGEST · ฟ้า = PROCESS+ARCHIVE · เขียว = CLEANUP
