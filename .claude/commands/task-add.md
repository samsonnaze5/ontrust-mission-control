---
description: เพิ่ม task ใหม่ใน tasks/inbox.csv — ถาม clarifying 2-3 ข้อก่อน เสนอ draft รอ user เห็นชอบแล้วค่อยเขียน
argument-hint: <task description ที่อยากเพิ่ม>
---

# /task-add — เพิ่ม task ใหม่ใน inbox

ผู้ใช้กำลังขอเพิ่ม task ใหม่ลงใน `tasks/inbox.csv`

## Input จาก user

$ARGUMENTS

## ขั้นตอน

### 1. โหลดบริบท

- อ่าน `tasks/inbox.csv` → ดู id ที่มีอยู่ (กัน collision) + format ของ row
- อ่าน `artifacts/INDEX.md` และ `artifacts/services.csv` ถ้ายังไม่ได้โหลดในเซสชันนี้ (เพื่อรู้ว่า service / db ไหนที่ task อาจอ้างถึง)
- ถ้า `$ARGUMENTS` ว่างหรือสั้นเกินจนตีความไม่ได้ → ถาม user ก่อนว่าอยากเพิ่ม task อะไร แล้วหยุดรอ

### 2. ถาม clarifying 2-3 ข้อ (ภาษาไทย ตาม CLAUDE.md §5)

เลือก **เฉพาะคำถามที่ "ขาดแล้วเขียน draft ไม่ได้"** — ห้ามถามเกิน 3 ข้อในรอบเดียว ตัวอย่างหัวข้อที่มักขาด:

- target service / database คือไหน? (อ้าง `services.csv` / `databases.csv`)
- priority ระดับไหน? (P0 / P1 / P2 / P3)
- references ที่เกี่ยวข้อง? (file path, ticket id, brainstorming session, PR url)
- success criteria คืออะไร? (เกณฑ์ verify ได้ — ตาม CLAUDE.md §4)
- มี deadline / dependency กับ task อื่นไหม?

ถ้า `$ARGUMENTS` ระบุครบอยู่แล้ว → ข้ามไปข้อ 3 ได้เลย

### 3. เสนอ draft row (markdown table)

แสดง draft ให้ user ตรวจ — **ห้ามเขียน CSV ก่อน user confirm**

Columns ของ `tasks/inbox.csv`: `id, priority, title, description, references, notes, skip`

- **id** — random 12-char alphanumeric ผสม upper/lower/digit (เลี่ยง ambiguous chars `0 O l 1 I`) เช่น `Tk7mNp2VxQwR`, `xY9pQrZ4LmKt` — ตรวจไม่ซ้ำกับที่มีใน inbox.csv และ done.csv
- **priority** — P0 / P1 / P2 / P3
- **title** — สั้น ≤ 60 chars, action-oriented, ภาษาอังกฤษ
- **description** — ครบถ้วน, มี success criteria ภายใน, ภาษาอังกฤษ (artifact ตาม CLAUDE.md §5)
- **references** — คั่นด้วย `;` (เช่น `scripts/extract_schemas.py;CLAUDE.md#85;BL-017`)
- **notes** — context / เหตุผลที่เพิ่ม (เช่น `Spawned from brainstorming 2026-04-26 #28473`)
- **skip** — เว้นว่าง

### 4. รอ user confirm

- user ขอแก้ → ปรับ draft แล้วเสนอใหม่
- user OK → ไปข้อ 5

### 5. Append row ลง tasks/inbox.csv

- ใช้ **Edit tool** (ไม่ใช่ Bash echo) — preserve format เดิม
- CSV escaping: ถ้า field มี `,` `"` หรือ newline → wrap field ด้วย `"` และ escape `"` เป็น `""`
- ตรวจซ้ำว่า id ไม่ชนกับ row อื่น

### 6. รายงานผล (ภาษาไทย)

- บอก id ใหม่ที่เพิ่ม
- next step: แนะนำ `/task-discuss <id>` ถ้ารายละเอียดยังไม่ลึกพอ หรือ `/task-do <id>` ถ้าพร้อมรัน

## ข้อห้ามสำคัญ

- ห้ามเขียน CSV ก่อน user confirm
- ห้ามเดา service / priority — ถ้าไม่ชัด ต้องถาม
- ห้ามตั้ง `skip` ให้เอง (column นี้ user เป็นคนใช้ flag rows ที่ Claude ไม่ต้องแตะ)
- ภาษาที่ใช้สื่อสาร user: ไทย; เนื้อหาในไฟล์ CSV: อังกฤษ (ตาม CLAUDE.md §5)
