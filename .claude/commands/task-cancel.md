---
description: ยกเลิก task — ย้ายจาก inbox.csv ไป done.csv พร้อม summary=Cancelled และ commit=(cancelled)
argument-hint: <task-id> [reason]
---

# /task-cancel — ยกเลิก task

ผู้ใช้ขอยกเลิก task: `$ARGUMENTS`

## ขั้นตอน

### 1. Parse arguments

`$ARGUMENTS` format: `<id> [reason]` — reason ที่เหลือหลัง id

- ไม่มี id → ถาม user
- มีแค่ id ไม่มี reason → ถาม user **1 คำถาม**: "ยกเลิกเพราะอะไร? (ต้องระบุเพื่อ traceability)"
- **ห้ามยกเลิกโดยไม่มี reason** — เก็บไว้ใน done.csv `summary` เพื่อให้อ่านย้อนหลังเข้าใจ

### 2. หา task ใน inbox.csv

อ่าน `tasks/inbox.csv` → หา row ที่ id = id ที่ user ให้

- ไม่พบ → แจ้ง user + แสดง id ทั้งหมดใน inbox + STOP
- ถ้า row นั้น `skip` ไม่ว่าง → แสดงค่า skip ให้ user เห็น แล้วถามว่ายังจะ cancel หรือ unskip + เก็บไว้ดีกว่า

### 3. ยืนยันก่อนย้าย (CLAUDE.md §6)

แสดง user เป็น markdown:
- title
- description (truncate 200 chars ถ้ายาวเกิน)
- reason ที่จะบันทึก
- ถามยืนยัน: **"ย้าย task นี้ไป done.csv เป็น cancelled ใช่ไหม?"**

User ตอบ yes → ขั้นต่อไป
User ตอบ ไม่ / ลังเล / ขอแก้ → STOP (row คงอยู่ใน inbox ตามเดิม)

### 4. Move row inbox → done

ทำ 2 step ใน 2 tool calls (ไม่ atomic แต่ tolerable เพราะ user-driven):

**4a. ลบ row จาก `tasks/inbox.csv`** ด้วย Edit tool

**4b. Append row ลง `tasks/done.csv`** ด้วย Edit tool — column ที่ inbox มี + 5 column เพิ่ม:

| Column | Value |
|---|---|
| `completed_at` | ISO date วันนี้ (`YYYY-MM-DD`) |
| `commit` | `(cancelled)` — string literal ไม่ใช่ SHA |
| `summary` | `Cancelled: <reason>` |
| `retro_refs` | (เว้นว่าง) |
| `drift_resolution` | (เว้นว่าง) |

CSV escaping: `summary` มี `,` หรือ `"` → wrap ด้วย `"` และ escape `"` เป็น `""`

### 5. รายงาน (ภาษาไทย)

- บอก id ที่ cancel + ตอนนี้อยู่ใน `done.csv` แล้ว
- ย้ำว่า **ไม่มี undo** — ถ้าเปลี่ยนใจต้อง `/task-add` ใหม่ (id ใหม่ด้วย เดิมเก็บใน done เป็น audit trail)

## ข้อห้าม

- ห้าม cancel โดยไม่มี reason
- ห้าม cancel โดยไม่ confirm (CLAUDE.md §6)
- ห้ามใส่ commit SHA จริง — `(cancelled)` คือ marker บอกว่าไม่มีโค้ดเปลี่ยน
- ห้ามแตะ row อื่นใน inbox.csv หรือ done.csv
- ภาษาคุย: ไทย; เนื้อหา CSV (`summary`, etc.): อังกฤษ ตาม convention (CLAUDE.md §5)
