# Deal Pipeline — Sequence Diagram

ดูคู่กับ [flow.csv](flow.csv) — `[XX]` ในข้อความ = step number ใน flow.csv

```mermaid
sequenceDiagram
    participant MT5 as External MT5 PG
    participant K as Kafka
    participant DealsInIng as deals-in-ingestor<br/>(mt5-processor)
    participant DealsOutIng as deals-out-ingestor<br/>(mt5-processor)
    participant PosDet as position-detector<br/>(mt5-processor)
    participant RebCalc as rebate-calculator<br/>(financial-service)
    participant AccBld as accrual-builder<br/>(financial-service)
    participant SetSch as settlement-scheduler<br/>(financial-service)
    participant WTW as wallet-transaction-writer<br/>(financial-service)
    participant EarnCalc as earning-calculator<br/>(financial-service)
    participant Arch as 7 archivers<br/>(archived)
    participant Watch as cleanup-watcher<br/>(archived) [scaffold]
    participant Clean as 7 cleaners<br/>(archived)
    participant PG as Postgres<br/>crm_trading_* + crm_financial
    participant CH as ClickHouse<br/>client + ib

    rect rgba(255,235,205,0.4)
    Note over MT5,PG: INGEST — deal in
    MT5->>K: [01] debezium → mt5.deal.in.received
    K->>DealsInIng: [02] consume
    DealsInIng->>PG: [02] INSERT crm_trading_open.mt5_deals_in
    PG->>K: [03] debezium → mt5-processor.deal.in.created
    end

    rect rgba(255,235,205,0.4)
    Note over MT5,PG: INGEST — deal out (main rebate trigger)
    MT5->>K: [04] debezium → mt5.deal.out.received
    K->>DealsOutIng: [05] consume
    DealsOutIng->>PG: [05] INSERT crm_trading_closed.mt5_deals_out
    PG->>K: [06] debezium → mt5-processor.deal.out.created
    end

    rect rgba(220,235,250,0.4)
    Note over K,CH: PROCESS + ARCHIVE — fan-out 3 จาก deal.out.created
    par position completion (mt5-processor)
        K->>PosDet: [07] consume mt5-processor.deal.out.created
        PosDet->>PG: [07] match in/out + INSERT crm_trading_complete (only 100% closed)
        PG->>K: [08] debezium → mt5-processor.position.created
    and rebate calculation (financial-service)
        K->>RebCalc: [09] consume mt5-processor.deal.out.created
        RebCalc->>PG: [09] INSERT crm_financial.rebate_distributions
        RebCalc->>K: [09] publish financial.rebate.calculated (direct)
    and archive deal out
        K->>Arch: [18] consume mt5-processor.deal.out.created
        Arch->>CH: [18] batch INSERT clickhouse_client.mt5_deals_out
    end
    end

    rect rgba(220,235,250,0.4)
    Note over K,CH: PROCESS + ARCHIVE — fan-out 2 จาก rebate.calculated
    par accrual building (financial-service)
        K->>AccBld: [10] consume financial.rebate.calculated
        AccBld->>PG: [10] INSERT crm_financial.rebate_accruals (PENDING)
        PG->>K: [11] debezium → financial.rebate.accrual.created
    and archive rebate distribution
        K->>Arch: [20] consume financial.rebate.calculated
        Arch->>CH: [20] batch INSERT clickhouse_ib.rebate_distributions
    end
    end

    rect rgba(220,235,250,0.4)
    Note over SetSch,K: PROCESS — settlement scheduler (interval 2 นาที)
    loop interval 2 นาที (sleep หลังเสร็จ)
        SetSch->>PG: [12] SELECT PENDING accruals (batch 500 ต่อ user/wallet)
        SetSch->>PG: [12] INSERT rebate_settlements + UPDATE accruals → SETTLED
        PG->>K: [13] debezium → financial.rebate.settlement.created
    end
    end

    rect rgba(220,235,250,0.4)
    Note over K,CH: PROCESS + ARCHIVE — fan-out 2 จาก settlement.created
    par wallet transaction writer (financial-service)
        K->>WTW: [14] consume financial.rebate.settlement.created
        WTW->>PG: [14] INSERT wallet_transactions REBATE_CREDIT (idempotent ผ่าน uq_wallet_txn_reference)
        PG->>K: [15] debezium → financial.wallet.transaction.created
    and archive settlement
        K->>Arch: [22] consume financial.rebate.settlement.created
        Arch->>CH: [22] batch INSERT clickhouse_ib.rebate_settlements
    end
    end

    rect rgba(220,235,250,0.4)
    Note over K,CH: PROCESS + ARCHIVE — fan-out 2 จาก wallet.transaction.created
    par IB earning aggregate (financial-service)
        K->>EarnCalc: [16] consume financial.wallet.transaction.created
        EarnCalc->>PG: [16] UPDATE IB earning aggregate (write-only)
    and archive wallet transaction
        K->>Arch: [23] consume financial.wallet.transaction.created
        Arch->>CH: [23] batch INSERT clickhouse_ib.wallet_transactions
    end
    end

    rect rgba(220,250,235,0.4)
    Note over K,CH: ARCHIVE — async consumers ที่เหลือ (independent)
    K->>Arch: [17] consume mt5-processor.deal.in.created
    Arch->>CH: [17] batch INSERT clickhouse_client.mt5_deals_in
    K->>Arch: [19] consume mt5-processor.position.created
    Arch->>CH: [19] batch INSERT clickhouse_client.mt5_position_completes
    K->>Arch: [21] consume financial.rebate.accrual.created
    Arch->>CH: [21] batch INSERT clickhouse_ib.rebate_accruals
    end

    rect rgba(220,255,220,0.4)
    Note over Watch,Clean: CLEANUP — interval ~15 นาที (fan-out 7 cleaners)
    loop interval ~15 นาที (sleep หลังเสร็จ)
        Watch->>CH: [24] SELECT verify archived (client + ib)
        Watch->>PG: [24] SELECT settlements status=COMPLETED
        Watch->>K: [24] publish paid.clean (multi-key shape)
        Note over K,Clean: 7 cleaners — consumer group แยก filter ด้วย key shape
        K->>Clean: [25] paid.clean (deal_id)
        Clean->>PG: [25] DELETE crm_trading_open.mt5_deals_in
        K->>Clean: [26] paid.clean (deal_id)
        Clean->>PG: [26] DELETE crm_trading_closed.mt5_deals_out
        K->>Clean: [27] paid.clean (position_id)
        Clean->>PG: [27] DELETE crm_trading_complete.mt5_position_completes
        K->>Clean: [28] paid.clean (deal_id)
        Clean->>PG: [28] DELETE crm_financial.rebate_distributions
        K->>Clean: [29] paid.clean (deal_id)
        Clean->>PG: [29] DELETE crm_financial.rebate_accruals
        K->>Clean: [30] paid.clean (settlement_id)
        Clean->>PG: [30] DELETE crm_financial.rebate_settlements
        K->>Clean: [31] paid.clean (wallet_transaction_id)
        Clean->>PG: [31] DELETE crm_financial.wallet_transactions
    end
    end

    Note over Watch,Clean: TBD — step 32 rebate-accrual-scheduler (scaffold ใน archived service — ดู flow.csv)
```

## Legend

- **[scaffold]** — binary มีอยู่แต่ยังเป็น stub (tick log TODO เฉยๆ) ต้อง implement ให้ทำงานจริง
- **[missing]** — ยังไม่มี binary ตัวนี้ ต้องสร้างใหม่
- สีกล่อง: ส้ม = INGEST · ฟ้า = PROCESS+ARCHIVE · เขียวอ่อน = ARCHIVE-only · เขียว = CLEANUP
- `par/and` block = consumers หลายตัว consume topic เดียวกัน (fan-out)
- `loop` block = cron / interval worker
