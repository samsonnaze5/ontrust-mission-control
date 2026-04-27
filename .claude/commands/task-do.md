---
description: Run task ที่อยู่ใน tasks/inbox.csv ตาม CLAUDE.md §8.2 Task Bootup Procedure — auto-move ไป done.csv เมื่อสำเร็จ
argument-hint: <task-id>
---

# /task-do — Run task จาก inbox

ผู้ใช้ขอให้รัน task id: `$ARGUMENTS`

ปฏิบัติตาม **CLAUDE.md §8.2 Task Bootup Procedure** อย่างเคร่งครัด ทุก fork สำคัญ → STOP & ASK (§6)

## Phase 1 — Locate task

1. โหลด CLAUDE.md (ถ้ายังไม่ได้อ่านในเซสชันนี้)
2. ค้น row ที่ id = `$ARGUMENTS` ใน `tasks/inbox.csv`
   - ไม่พบ → แจ้ง user + แสดง id ทั้งหมดที่มีอยู่ + STOP
   - พบแต่ `skip` column ไม่ว่าง → แจ้ง user + ถามว่าจะ override flag ไหม
3. Parse → identify:
   - target service (จาก description / references / notes)
   - artifact dependencies (schemas / conventions / pipelines ที่ task ต้องใช้)
   - DB ที่เกี่ยวข้อง (จาก `databases.csv`)
4. ถ้า task ไม่ระบุ service ชัด → **STOP & ASK** (CLAUDE.md §8.3) ห้ามเดา

## Phase 2 — Drift check (CLAUDE.md §8.2 step 2)

1. เปิด `_meta.csv` ของ artifact set ที่เกี่ยวข้อง
2. ถ้า `extracted_by=bootstrap` → SHA เป็น placeholder (`EXAMPLE_SHA_*`) → **stale แน่นอน** → ASK refresh
3. `cd` ไป target repo path (จาก `services.csv`) → `git rev-parse HEAD`
4. เทียบกับ `source_commit_sha` ใน `_meta.csv`
5. ถ้าต่าง → แสดง user: `drift: artifact at SHA-A, target at SHA-B (N commits ahead)`
6. ASK 3 ทาง: **refresh now** / **proceed stale** / **abort**
7. **เก็บ decision** ไว้สำหรับ `drift_resolution` column ใน done.csv (`refreshed` / `proceed-stale` / `none`)

## Phase 3 — Read artifacts (CLAUDE.md §8.2 step 3 — ลำดับสำคัญ)

โหลดเฉพาะที่ task ต้องใช้ — อย่าโหลดทั้งหมด:

1. `artifacts/INDEX.md` (ถ้ายังไม่อ่าน)
2. `artifacts/services.csv` — confirm path + branch ของ target service
3. `artifacts/conventions/<service>/*.md` — ทุกไฟล์ที่มี (status `stable` เท่านั้นที่ใช้ได้ — `draft`/`deprecated` ห้าม lock-in ตาม §8.4)
4. `artifacts/schemas/<db>/` — เฉพาะ DB ที่ task เกี่ยว (เริ่มจาก `_index.csv` → `_tables.csv` → `tables/<table>.csv`)
5. target repo's `CLAUDE.md` / `AGENTS.md` ถ้ามี

## Phase 4 — Plan & Execute

1. **เสนอ plan สั้น 3-6 bullets** ภาษาไทย → **รอ user go-ahead** (CLAUDE.md §6)
   - แต่ละ bullet มี verify check (CLAUDE.md §4)
2. Verify path target มีจริง (`os.path.exists` / `ls`) ก่อนแก้โค้ด — fail fast
3. เขียนโค้ดที่ **target repo เท่านั้น** — ห้ามแก้ `.go` `.py` ฯลฯ จาก mission-control (§8.3)
4. ห้ามเขียน test proactively — ถ้า task ขอ test → STOP & ASK pattern (§8.5 ยังไม่มี testing convention)
5. ถ้า convention doc ขัดกับโค้ดจริง → STOP & ASK + flag ใน retro (§8.4)
6. ถ้า convention status = `draft` → ห้าม lock-in pattern นั้น

## Phase 5 — Commit & Post-task

1. **Commit ที่ target repo** (ไม่ใช่ที่ mission-control)
   - ทำตาม convention ของ target repo
   - **ขอ user confirm ก่อน commit** — ห้าม auto-commit
2. ดึง commit SHA (short form 7 chars) ที่เพิ่ง commit
3. **เขียน retrospective** ตาม CLAUDE.md §7 — ระบุ severity tags + 5-digit ref ids (`#10000`–`#99999`)
4. **Move row inbox → done** ใน mission-control:
   - ลบ row ออกจาก `tasks/inbox.csv` (Edit tool)
   - Append ลง `tasks/done.csv` พร้อม columns เพิ่ม:
     - `completed_at` — ISO date วันนี้ (YYYY-MM-DD)
     - `commit` — short SHA จาก step 2
     - `summary` — 1-2 ประโยค สรุปผลงาน (ภาษาอังกฤษ)
     - `retro_refs` — id retro คั่น `;` (เช่น `#41827;#62094`)
     - `drift_resolution` — จาก Phase 2 step 7
5. **Trigger refresh ที่จำเป็น** (CLAUDE.md §8.2 step 6):
   - แก้ schema → `task schemas:refresh` หรือ `task schemas:refresh:db -- <db>`
   - แก้ enum → `task enums:extract`
   - add/rename/delete `cmd/*` → `task entrypoints:refresh`
6. **Commit ที่ mission-control** (artifact updates / inbox.csv / done.csv) — **รอ user ขอก่อน** ห้าม auto-commit (§8.3)

## ข้อห้าม / ระเบียบสำคัญ

- ผู้ใช้หยุดกลางทาง / abort → row **ยังอยู่ที่ inbox.csv** ห้ามย้ายไป done.csv
- ภาษา: ไทย สำหรับสื่อสาร / อังกฤษ สำหรับ commit / PR / code (§5)
- ทุก fork สำคัญ (drift refresh / plan execute / destructive op / commit) → STOP & ASK (§6)
- Path target → ใช้ absolute path จาก `services.csv` เท่านั้น ห้าม resolve relative (§8.3)
- ห้ามแก้ artifact human-curated (services.csv / databases.csv / envs.csv / conventions / pipeline docs / terraform-modules.csv) โดยอัตโนมัติ — propose ใน retro (§8.7)
