---
description: ตั้ง skip flag ใน tasks/inbox.csv — บอก Claude ว่าอย่าหยิบ task นี้ทำเอง row ยังอยู่ใน inbox
argument-hint: <task-id> <reason>
---

# /task-skip — ตั้ง skip flag

ผู้ใช้ขอ skip task: `$ARGUMENTS`

## ขั้นตอน

### 1. Parse arguments

`$ARGUMENTS` มี format: `<id> <reason>` — id เป็นคำแรก, reason คือส่วนที่เหลือ

- argument ว่าง → ถาม user ทั้ง id และ reason
- มีแค่ id → ถาม user: "เหตุผลที่ skip คืออะไร?"
- id format ผิดปกติ (ไม่ใช่ 12 chars / มี space แปลกๆ ระหว่างอักษร) → confirm กับ user ก่อน

### 2. หา task ใน inbox.csv

อ่าน `tasks/inbox.csv` → หา row ที่ id = id ที่ user ให้

- ไม่พบ → แจ้ง user + แสดง id ทั้งหมดใน inbox + STOP
- พบแล้ว `skip` column ไม่ว่างอยู่แล้ว → แสดงค่าปัจจุบัน + ถามยืนยันว่าจะ overwrite ไหม

### 3. Update row

- ใช้ **Edit tool** — แก้เฉพาะ `skip` column ของ row นั้น เป็น `<reason>`
- CSV escaping: ถ้า reason มี `,` `"` หรือ newline → wrap ด้วย `"` และ escape `"` เป็น `""`
- **ห้ามแตะ column อื่น** ของ row นี้ และ row อื่นห้ามแตะเลย

### 4. รายงาน (ภาษาไทย)

- บอก id + reason ที่ตั้ง
- ย้ำว่า task **ยังอยู่ใน inbox.csv** (skip ≠ cancel) — Claude แค่ไม่หยิบมาทำเอง
- ถ้าอยาก unskip → user แก้ column `skip` เป็นค่าว่างใน inbox.csv ตรงๆ (command นี้ไม่ทำ unskip — ป้องกัน accidental clear)
- ถ้าอยากย้ายไป done เลย → แนะนำ `/task-cancel <id> <reason>` แทน

## ข้อห้าม

- ห้ามย้าย row ไป done.csv (skip ≠ cancel)
- ห้ามแก้ column อื่นของ row นี้
- ห้ามแก้ row อื่น
- ห้าม clear skip ของ row อื่นๆ ที่ skip ไว้แล้ว
- ภาษาคุย: ไทย; reason ใน CSV: user เลือกได้ (ไทยหรืออังกฤษ — เป็น free-form metadata)
