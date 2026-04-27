ใช้ Agent `git-pr-craft-v2` วิเคราะห์ feature branch แล้วสร้าง PR description (v2 optimized)

$ARGUMENTS

ใช้ SKILL `git-craft-v2` ทำตามขั้นตอน:
1. รัน `bash .claude/skills/git-craft-v2/scripts/collect_pr_fast.sh` เก็บข้อมูล branch + detect tests (script เดียว)
2. อ่าน `.claude/skills/git-craft-v2/references/pr-template-skeleton.md` แล้วเติมทุก section
3. วิเคราะห์ security + improvement suggestions จาก actual diffs
4. Save เป็น `outputs/pr-description.md`
5. สื่อสารเป็นภาษาไทย
