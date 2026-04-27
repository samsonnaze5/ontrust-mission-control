---
description: สรุป tasks ใน inbox.csv และ/หรือ done.csv (read-only)
argument-hint: [inbox|done|all]  (default: inbox)
---

# /task-list — สรุป tasks

ผู้ใช้ขอดูรายการ tasks scope: `$ARGUMENTS`

## ขั้นตอน

### 1. กำหนด scope จาก argument

- ว่าง / `inbox` → แสดงเฉพาะ `tasks/inbox.csv` (default)
- `done` → แสดงเฉพาะ `tasks/done.csv`
- `all` → แสดงทั้งสอง (inbox ก่อน → done)
- ค่าอื่นๆ → แจ้ง user ว่ารองรับแค่ 3 ค่านี้ + STOP

### 2. อ่านไฟล์

- inbox: `tasks/inbox.csv`
- done: `tasks/done.csv`

### 3. แสดงผล

#### Inbox section (ถ้าอยู่ใน scope)

หัวเรื่อง: `## Inbox (active: A · skipped: S)`
- A = จำนวน row ที่ `skip` column ว่าง
- S = จำนวน row ที่ `skip` column ไม่ว่าง

ตาราง markdown — column ที่แสดง: `id`, `priority`, `title`, `references`
- เรียง priority ascending (`P0` → `P3`); ภายใน priority เดียวกัน คงลำดับเดิมในไฟล์
- truncate `title` ที่ 60 chars / `references` ที่ 50 chars (ถ้าเกินใส่ `…`)
- ถ้ามี row `skip` ไม่ว่าง → แสดงตารางย่อยอีกอัน หัว `### Skipped` พร้อม column `id`, `title`, `skip`

ถ้า inbox ว่าง → แจ้ง `Inbox เคลียร์แล้ว — ไม่มี active task`

#### Done section (ถ้าอยู่ใน scope)

หัวเรื่อง: `## Done (showing N of M)` — N = ที่แสดง (≤ 20), M = total
- limit 20 rows ล่าสุด เรียง `completed_at` descending
- ถ้า M > 20 → ใต้ตาราง: `… มีอีก (M-20) rows เก่ากว่า ดูใน tasks/done.csv ตรงๆ`

ตาราง — column ที่แสดง: `completed_at`, `id`, `priority`, `title`, `commit`, `summary`
- truncate `summary` ที่ 80 chars
- ถ้า `commit` = `(cancelled)` → แสดงตามจริง (mark ว่ายกเลิก)

### 4. รายงาน suggested actions (ภาษาไทย)

หลังตาราง:
- ถ้ามี `P0` ใน inbox → แนะนำ `/task-do <id-ของ-P0>` ก่อน
- ถ้ามี row ที่ `description` < 100 chars → แนะนำ `/task-discuss <id>` เพราะอาจรายละเอียดน้อย
- ถ้า inbox ว่างหมด → ชวน `/task-add` เพิ่ม

## ข้อห้าม

- **read-only command** — ห้าม edit ไฟล์ใดๆ
- ห้ามใส่ emoji ใน output (ตาม CLAUDE.md §5 / system prompt)
- ภาษา: ไทย สำหรับ heading + commentary; ตาราง: คงเนื้อหาเดิมจาก CSV (อังกฤษ)
