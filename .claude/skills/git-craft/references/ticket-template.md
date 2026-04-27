# Ticket Template (ClickUp Standard)

Template นี้ใช้สำหรับ reverse-engineer จาก PR description กลับเป็น ClickUp ticket
ทุก section ต้องมีอยู่เสมอ ถ้า section ไหนไม่เกี่ยวข้องให้เขียน "ไม่มี"
ภาษาหลักคือภาษาไทย technical terms คงเป็น English

---

## Template

```markdown
# [TICKET_TYPE] Ticket Title

> **Ticket Type:** Feature / Bug Fix / Improvement / Hotfix / Chore
> **Priority:** 🔴 Urgent / 🟠 High / 🟡 Medium / 🟢 Low
> **Estimated Story Points:** X
> **Labels:** label1, label2, label3
> **Sprint Suggestion:** Current Sprint / Next Sprint / Backlog

---

## 📖 รายละเอียด (Description)

<!-- สรุปสิ่งที่ต้องทำในภาพรวม เขียนให้ PM/PO เข้าใจได้โดยไม่ต้องอ่าน code
     เน้นว่า "ทำอะไร" และ "ทำไม" ไม่ต้องลงรายละเอียด technical มากเกินไป -->

## 🎯 วัตถุประสงค์ (Objective)

<!-- เป้าหมายหลักของ ticket นี้ เขียนให้ชัดเจน วัดผลได้
     เช่น "เพิ่มระบบ JWT authentication เพื่อให้ API endpoints มีความปลอดภัย" -->

## 📋 Acceptance Criteria

<!-- เงื่อนไขที่ต้องผ่านก่อนจะปิด ticket ได้ เขียนเป็นข้อๆ ที่ตรวจสอบได้จริง -->

- [ ] เงื่อนไข 1
- [ ] เงื่อนไข 2
- [ ] เงื่อนไข 3

## 📌 Sub-Tasks

<!-- แตก task ย่อยตาม module/feature area ที่เปลี่ยนแปลง
     แต่ละ sub-task ควรเป็นหน่วยงานที่สามารถทำเสร็จได้อิสระ -->

- [ ] **Sub-task 1:** คำอธิบาย
  - ไฟล์ที่เกี่ยวข้อง: `path/to/file`
  - รายละเอียด: ...
- [ ] **Sub-task 2:** คำอธิบาย
  - ไฟล์ที่เกี่ยวข้อง: `path/to/file`
  - รายละเอียด: ...

## 🔧 Technical Notes

<!-- หมายเหตุทาง technical สำหรับ developer ที่จะหยิบงานนี้ไปทำ
     เช่น library ที่ต้องใช้, pattern ที่ควรตาม, ข้อจำกัดที่ต้องระวัง -->

## 🔗 Dependencies

<!-- ticket หรือ system อื่นที่ต้องทำก่อน หรือที่จะได้รับผลกระทบ -->

- Blocked by: ไม่มี / [TICKET-ID]
- Blocks: ไม่มี / [TICKET-ID]
- Related: ไม่มี / [TICKET-ID]

## ✅ Definition of Done

- [ ] Code merged to target branch
- [ ] Tests pass
- [ ] Code reviewed and approved
- [ ] Documentation updated (if applicable)
- [ ] No regressions introduced
```

---

## Reverse-Engineering Guidelines

กระบวนการ "คิดย้อนกลับ" จาก PR Description → Ticket มีหลักการดังนี้:

### Ticket Type
วิเคราะห์จาก branch name prefix และ PR content:
- `feature/*` → Feature
- `fix/*` → Bug Fix
- `hotfix/*` → Hotfix
- refactoring-heavy PR → Improvement
- deps/CI/config changes → Chore

### Priority
ประเมินจาก PR description sections:
- ถ้า "ถ้าไม่ทำจะเป็นยังไง" มีผลกระทบรุนแรง (data loss, security hole, production down) → 🔴 Urgent
- ถ้ามี Breaking Changes → 🟠 High
- ถ้าเป็น feature ใหม่ที่มีผลกระทบปานกลาง → 🟡 Medium
- ถ้าเป็น improvement/chore ที่ไม่เร่งด่วน → 🟢 Low

### Story Points
ประมาณจากขนาดของ PR:
- 1-3 files, เปลี่ยนแปลงน้อย → 1-2 points
- 4-8 files, หลาย modules → 3-5 points
- 8+ files, cross-cutting concerns, breaking changes → 8-13 points

### Labels/Tags
ดึงจาก:
- Scope ของ commit messages (เช่น auth, api, db)
- ประเภทของ files ที่เปลี่ยน (frontend, backend, infrastructure)
- Branch prefix (feature, fix, hotfix)

### Sub-Tasks Breakdown
วิเคราะห์จาก PR changes แล้วจัดกลุ่มตาม module/concern:
- แต่ละ commit group หรือ directory ที่เปลี่ยนแปลง → 1 sub-task
- Test files → sub-task แยก (ถ้ามี test เยอะพอ)
- Documentation → sub-task แยก (ถ้ามี)
- Migration/Schema changes → sub-task แยก เสมอ (เพราะต้อง deploy ลำดับที่ถูกต้อง)

### Acceptance Criteria
แปลงจาก PR content:
- จาก "วัตถุประสงค์" → เป้าหมายที่ต้องบรรลุ
- จาก "วิธีการทดสอบ" → สิ่งที่ต้อง verify ได้
- จาก "Breaking Changes" → migration ต้องสำเร็จ
- จาก "ผลการทดสอบ" → tests ต้อง pass

### Technical Notes
ดึงจาก:
- Libraries/dependencies ที่เพิ่มใหม่ (จาก go.mod, package.json ฯลฯ)
- Design patterns ที่ใช้ (จากการวิเคราะห์ code structure)
- Breaking changes และ migration steps
- ข้อจำกัดหรือ trade-offs ที่เห็นจาก diff

### Description Tone
เขียนในมุมมองของ PM/PO — ไม่ใช่ developer:
- เน้น "ทำอะไร" และ "ทำไม" มากกว่า "ทำยังไง"
- ใช้ภาษาที่ business stakeholder เข้าใจได้
- ลด jargon ทาง technical ให้น้อยที่สุดใน Description และ Objective
- Technical details ให้อยู่ใน Technical Notes section
