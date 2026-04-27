---
description: เติมรายละเอียด task ใน tasks/inbox.csv ผ่าน structured brainstorm — ถามทีละหัวข้อตามแม่แบบ
argument-hint: <task-id>
---

# /task-discuss — เติมรายละเอียด task ผ่าน structured discussion

ผู้ใช้อยาก brainstorm / เติมรายละเอียด task id: `$ARGUMENTS`

## ขั้นตอน

### 1. โหลด task ปัจจุบัน

1. อ่าน `tasks/inbox.csv` → หา row ที่ id = `$ARGUMENTS`
2. ไม่พบ → แจ้ง user + แสดง id ทั้งหมดที่มี + STOP
3. แสดง row ปัจจุบันให้ user เห็น (markdown table — title, priority, description, references, notes)
4. โหลด `artifacts/INDEX.md` + `services.csv` + `databases.csv` ถ้ายังไม่ได้อ่าน — เพื่ออ้างถึง service / db ได้ถูกต้องระหว่างคุย

### 2. เดิน structured template — ถาม **1 หัวข้อต่อรอบ**

ห้ามรวมทุกหัวข้อเป็นรอบเดียว — ถามทีละหัวข้อ user ตอบเสร็จแล้วค่อยถัดไป
**ข้ามได้ทันที** ถ้า description ปัจจุบันระบุหัวข้อนั้นชัดอยู่แล้ว — แจ้ง user ว่าข้ามเพราะอะไร

#### (1) Goal — เป้าหมายจริงคืออะไร

- task นี้เสร็จแล้ว อะไรเปลี่ยน?
- ใครได้ประโยชน์? (service / team / stakeholder)
- ทำไมต้องตอนนี้? (deadline / dependency / incident)

#### (2) Scope — รวม / ไม่รวมอะไร

- in-scope: ไฟล์ / service / feature ที่ต้องแตะแน่นอน
- out-of-scope: ไฟล์ / feature ที่ "อย่าเผลอแก้" แม้เห็นระหว่างทาง (ตรงกับ CLAUDE.md §3 surgical changes)
- assumptions: สมมติฐานที่ task ตั้งอยู่บน

#### (3) Success Criteria — verify ได้ยังไง

- เกณฑ์ที่บอกได้ว่า "เสร็จ" (ตาม CLAUDE.md §4)
- transform เป็น verifiable goal — ตัวอย่าง:
  - "Add validation" → "test invalid inputs ผ่านทุก case"
  - "Fix bug" → "test reproduce bug ผ่าน"
  - "Refactor" → "test ก่อน/หลัง pass เท่ากัน"

#### (4) Edge Cases & Risks

- input / state ผิดปกติที่ต้องรองรับ
- destructive op ที่ต้องระวัง (DB migration / schema change / env var rename / breaking API)
- backward compat / legacy concern
- ผลกระทบกับ pipeline อื่น / service ปลายน้ำ

#### (5) References — แหล่งข้อมูลเพิ่มเติม

- ไฟล์ / ticket / PR / Slack / brainstorming session ที่เกี่ยวข้อง
- artifacts ที่ต้องโหลดตอน run (schemas / conventions / pipeline docs)
- mockup / spec / design doc

#### (6) Constraints

- tech stack ที่ใช้ / ห้ามใช้
- convention ที่ต้องผ่าน (ถ้า convention status = `draft` หรือไม่มี — flag ไว้)
- timeline / order dependency กับ task อื่น
- resource limits (CPU / memory / API quota)

### 3. ระหว่างคุย — สังเกต 2 สัญญาณ

- **Task ใหม่ที่ควรแยก** → ถ้าระหว่าง brainstorm พบ scope ที่ใหญ่จนควรเป็น task แยก → เสนอ user ตัดออกเป็น task แยก แนะนำ `/task-add` หลังจบรอบนี้
- **Convention gap** → ถ้าพบเรื่องที่ควรเป็น convention (testing / dependencies / structure / logging) → flag ไว้สำหรับ retro

### 4. สรุป updated draft

หลังเก็บข้อมูลครบ (หรือผ่านทุกหัวข้อแล้ว):

1. แสดง draft updated row (markdown table)
   - **id** เดิม (ห้ามเปลี่ยน)
   - **title** อาจ refine ใหม่ถ้า scope ชัดขึ้น
   - **description** ใหม่ที่รวม Goal + Scope + Success Criteria + Edge Cases (ภาษาอังกฤษ — เป็น artifact ตาม §5)
   - **references** รวมที่ user ให้
   - **notes** เพิ่มท้าย: `Refined via /task-discuss <YYYY-MM-DD>`
   - **priority** ปรับถ้าจำเป็น (เช่น พบว่าเร่งด่วนกว่าเดิม)
2. **รอ user confirm** ก่อน update CSV
3. user OK → **Edit tool** update row ใน `tasks/inbox.csv` (id เดิม content ใหม่)

### 5. รายงาน next step (ภาษาไทย)

- task พร้อมรัน → แนะนำ `/task-do <id>`
- ยังเปิดประเด็น → list ใน notes พร้อมหัวข้อที่ค้าง
- แตก task ใหม่ออกได้ → แจ้ง user ใช้ `/task-add`

## ข้อห้าม / ระเบียบ

- ห้ามอัด 6 หัวข้อในรอบเดียว — เดินทีละข้อ
- หัวข้อใด user ตอบสั้นเกิน → ถามต่อได้ 1 ครั้ง ห้าม pressure เกิน
- ห้าม update CSV ก่อน user confirm
- ห้ามเปลี่ยน id (ถ้าจะแยก task ใหม่ → ใช้ `/task-add` แยกต่างหาก)
- ภาษาที่ใช้คุย: ไทย; เนื้อหาใน CSV: อังกฤษ (CLAUDE.md §5)
