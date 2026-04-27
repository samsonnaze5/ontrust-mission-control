ใช้ Agent `git-commit-craft` วิเคราะห์ uncommitted changes แล้วสร้าง commit messages

$ARGUMENTS

ใช้ SKILL `git-commit-craft` ทำตามขั้นตอน:
1. รัน `bash .claude/skills/git-craft/scripts/collect_uncommitted.sh` เก็บข้อมูล changes
2. รัน `bash .claude/skills/git-craft/scripts/detect_change_groups.sh` วิเคราะห์ grouping
3. สร้าง commit plan พร้อม Conventional Commits format
4. **ตรวจสอบ Documentation Impact** — หลังได้ commit plan แล้ว ต้องวิเคราะห์ว่า changes ที่เกิดขึ้นมีผลกระทบต่อเอกสารหลัก 3 ไฟล์นี้หรือไม่:
   - `README.md` — project structure, features, server descriptions, shared packages
   - `CLAUDE.md` — domain modules tree, shared packages, key patterns, naming conventions
   - `_bmad-output/project-context.md` — implementation rules, anti-patterns, package naming, workflows

   **สิ่งที่ต้อง Impact จริงๆถึงจะอัพเดท** (ไม่ใช่ทุก commit):
   - เพิ่ม/ลบ subdomain module ใหม่ → อัพเดท directory tree
   - เพิ่ม shared package ใหม่ใน `pkg/` → อัพเดท shared packages list
   - เปลี่ยน server architecture (port, domains) → อัพเดท server table
   - เพิ่ม naming convention หรือ pattern ใหม่ → อัพเดท rules/patterns
   - เพิ่ม anti-pattern ที่เจอจากการแก้บั๊ก → อัพเดท anti-patterns list

   ถ้ามี impact → **เพิ่มเป็น commit แยก** (ใช้ `docs: update project documentation`) ไว้ท้ายสุดของ commit plan
5. แสดง copy-paste commands ให้ user
6. สื่อสารเป็นภาษาไทย ไม่ auto-commit
