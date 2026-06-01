# CHANGELOG — ai-stack

> งานที่ทำเสร็จแล้ว เรียงตามวัน (ล่าสุดอยู่บน). งานค้าง → [ROADMAP.md](ROADMAP.md).

---

## 2026-06-01 — Phase 0: Preflight ผ่าน

- รัน `scripts/00-preflight.sh` ครั้งแรก — ผ่านทุกข้อ ✓
  - GPU: RTX 3060 Laptop 6144 MiB ✓
  - ดิสก์ว่าง: 784 GB ✓ (threshold ≥30 GB)
  - RAM: 35 GB ✓
  - เน็ต IPv4: ✓ (curl4 บังคับ -4 ตาม GOTCHAS #1)
  - Docker: 29.5.2 ✓
- Advisor ตรวจทานสคริปต์: lib.sh idempotent ✓, IPv4 enforcement ✓, sudo warning ✓
- พร้อมรัน Phase A (`scripts/phase-a-ollama.sh`)

---

## 2026-06-01 — Repo init

- เคลียร์ไฟล์เดิม (สำรองไว้ `.backup-pre-init-20260601/`: docker-compose Open WebUI + Modelfile ChindaMT)
- วางโครงสร้าง Living Docs governance ปรับจาก `vigil-platform` (decision rules + documentation rules)
- เขียน CLAUDE.md (entry point: working agreement, model assignment, doc map)
- วางแผน Phase A–D ใน ROADMAP.md + สคริปต์ติดตั้งใน `scripts/` (เตรียมไว้ ยังไม่รัน)
- เก็บ config: `compose/docker-compose.yml` (Open WebUI), `models/ChindaMT-4B.Modelfile`, `config/continue-config.json`
- เพิ่ม Phase B+ : expose `ai.dojojin.tech` ผ่าน tunnel เดิม — `scripts/phase-b-expose-cloudflare.sh` + `docs/REF_cloudflare-tunnel.md` (ตรวจแล้ว: DNS + Cloudflare Access มีอยู่แล้ว, เหลือแค่ ingress rule)

> ยังไม่ได้ติดตั้งจริง — เฟส A–D + B+ สถานะ ⬜ ทั้งหมด (เขียนโค้ด/เอกสารเตรียมไว้).

---

*ai-stack CHANGELOG*
