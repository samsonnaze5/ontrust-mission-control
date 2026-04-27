# PR Template (v2 Skeleton)

ทุก section ต้องมี ถ้าไม่เกี่ยวข้องให้เขียน "ไม่มี"
ภาษาหลัก: ไทย | Technical terms: English | Emoji: คงไว้ตาม header

---

```markdown
## 📋 สรุปภาพรวม (Summary)

<!-- 2-3 ประโยคสรุป PR ให้เข้าใจทันที -->

## 🔗 ความเป็นมา (Background)

<!-- บริบทเบื้องหลัง ทำไมต้องมี PR นี้ อ้างอิง issue/ticket ถ้ามี -->

## 🎯 วัตถุประสงค์ (Objective)

<!-- เป้าหมายหลัก ชัดเจน วัดผลได้ -->

## 💡 ทำไปทำไม (Motivation)

<!-- ปัญหาที่ต้องการแก้ -->

## 🎯 ทำไปเพื่ออะไร (Purpose & Value)

<!-- คุณค่าที่ได้รับ ส่งผลดีต่อระบบ/ทีมอย่างไร -->

## ⚠️ ถ้าไม่ทำจะเป็นยังไง (Risk of Not Doing)

<!-- ความเสี่ยง/ผลกระทบถ้าไม่ทำ เขียนให้ concrete -->

## 📝 รายละเอียดการเปลี่ยนแปลง (Changes Detail)

<!-- จัดกลุ่มตาม module/feature area อธิบาย what + why -->

### ไฟล์ที่เปลี่ยนแปลง (Files Changed)

| ไฟล์ | ประเภท | รายละเอียด |
|------|--------|-----------|
| `path/to/file` | Added/Modified/Deleted | คำอธิบาย |

## 📊 Diagrams

<!-- เลือก 1-3 Mermaid diagrams ที่เหมาะสม:
     Flowchart (logic/decisions), Sequence (API chains), User Journey (UX),
     Mindmap (multi-module), Architecture (structural changes)
     ใช้ English labels, max 15-20 nodes. ถ้าแค่ config/docs → "ไม่มี" -->

## 💥 ผลกระทบ (Impact Analysis)

<!-- direct + indirect impact ต่อ downstream services, DB, API consumers -->

## ⚡ Breaking Changes

<!-- API signature เปลี่ยน, schema migration, config format เปลี่ยน ถ้าไม่มี → "ไม่มี" -->

## 🧪 วิธีการทดสอบ (How to Test)

<!-- ขั้นตอน reproducible: commands, endpoints, scenarios -->

## 🧪 ผลการทดสอบ (Testing Results)

### Test Files ที่เปลี่ยนแปลง

| ไฟล์ | สถานะ | รายละเอียด |
|------|--------|-----------|
| `path/to/test` | Added/Modified | คำอธิบาย |

### ผลการรัน Test

```
<!-- ผลลัพธ์จาก test run -->
```

**สถานะ:** ✅ PASS / ❌ FAIL / ⚠️ ไม่สามารถรันได้ / 📝 ยังไม่มี test

### Test Coverage แนะนำเพิ่มเติม

<!-- source files ที่ไม่มี test ครอบคลุม -->

## 📸 Screenshots / Evidence

<!-- UI → before/after, API → curl output, DB → migration output, Perf → benchmarks
     ใส่ actionable placeholder: > 📸 **TODO:** เพิ่ม screenshot แสดง ... -->

## 💡 Improvement Suggestions

### ระดับ: ควรทำ (Should Do)

<!-- สิ่งที่ป้องกันปัญหาจริง แต่ละ item มี:
     - ไฟล์ + เหตุผล
     - <details> block "🤖 Prompt for AI Agents" พร้อม Target/Action/Context/Dependencies -->

### ระดับ: น่าทำ (Nice to Have)

<!-- ทำให้ดีขึ้นแต่ไม่เร่งด่วน format เดียวกับ ควรทำ -->

## 🔐 Penetration Testing Suggestions

### 🎯 Attack Surfaces ที่ควรทดสอบ

| จุดที่ควรทดสอบ | ประเภทความเสี่ยง | ระดับ | วิธีทดสอบ |
|----------------|------------------|-------|----------|
| endpoint/function | ประเภท | 🔴/🟠/🟡 | วิธีทดสอบสั้นๆ |

### 📝 Security Recommendations

<!-- ข้อแนะนำ security เพิ่มเติม -->

## 🧪 Test Case Scenario Suggestions

### 🎯 High Priority (5-10 cases)

<!-- happy path, critical business logic
     | # | Scenario | ประเภท | Priority |
     Steps + Expected Result -->

### 🔄 Regression (3-5 cases)

<!-- existing features ที่อาจได้รับผลกระทบ -->

### 🧩 Edge Cases (3-5 cases)

<!-- null/empty, concurrent, permission boundaries -->

### 📊 Coverage Summary

<!-- สรุป coverage % ของ test cases -->

## ✅ Checklist

- [ ] Code follows project conventions
- [ ] Tests added/updated
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or documented)
- [ ] Self-reviewed code
- [ ] Security reviewed
```
