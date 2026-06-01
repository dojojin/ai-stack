# CHANGELOG — ai-stack

> งานที่ทำเสร็จแล้ว เรียงตามวัน (ล่าสุดอยู่บน). งานค้าง → [ROADMAP.md](ROADMAP.md).

---

## 2026-06-01 — Phase C: OpenClaw local brain ✅

- ติดตั้ง `openclaw@latest` ผ่าน npm (Node 22.22.0, IPv4-first)
- config `~/.openclaw/openclaw.json`: gateway bind=loopback, provider=ollama/127.0.0.1:11434, channels ปิดทั้งหมด
- exec-approvals: security=allowlist, askFallback=deny (ถามก่อนรัน command)
- ปิด memorySearch (ไม่มี OpenAI key — ใช้ local เท่านั้น)
- ติดตั้ง `openclaw-gateway.service` (systemd user) + `loginctl enable-linger`
- gateway HTTP 200 ที่ `http://127.0.0.1:18789/` ✓
- models เห็น 3 ตัว: `qwen2.5-coder:7b` (default), `:3b`, `qwen2.5:7b` — local=yes ทั้งหมด
- Advisor verify: bind=loopback ✓, channels=none ✓, inference ผ่าน Ollama ✓
- warnings ที่รอ Phase D: `commands.ownerAllowFrom` (ต้องการ channel ID) + secrets migration

---

## 2026-06-01 — Phase B+: Expose ai.dojojin.tech ✅

- เพิ่ม ingress rule `ai.dojojin.tech → http://127.0.0.1:3000` ใน `~/.cloudflared/config-host.yml` (ก่อน catch-all 404)
- สำรอง config ก่อนแก้ (`.bak-20260601-210441`)
- restart `cloudflared-dojojin.service` สำเร็จ
- Verify: `dojojin.tech` ยัง HTTP 200 ✓, `ai.dojojin.tech` ได้ HTTP 302 (Cloudflare Access login) ✓ ไม่ใช่ 404/502
- แก้ bug: flag `--config` ใน `cloudflared tunnel ingress validate/rule` ผิดตำแหน่ง → แก้เป็น `cloudflared --config FILE tunnel ingress ...`

---

## 2026-06-01 — Phase B: Open WebUI + Continue.dev ✅

- ดึง image `ghcr.io/open-webui/open-webui:main` + รัน container port `3000→8080`
- HTTP 200 ที่ `http://localhost:3000` ✓
- วาง Continue config → `~/.continue/config.json` (chat=qwen2.5-coder:7b, autocomplete=:3b)
- **แก้ปัญหา Ollama bind:** Ollama default bind `127.0.0.1` → container เข้าไม่ได้
  - เพิ่ม `/etc/systemd/system/ollama.service.d/override.conf` → `OLLAMA_HOST=0.0.0.0:11434`
  - restart ollama → container→Ollama ต่อได้ (`host.docker.internal:11434`) ✓
- Advisor verify: WebUI healthy, container เห็น 3 โมเดล ✓
- ขั้นตอน manual ที่เหลือ: สมัคร admin ที่ `http://localhost:3000` + ติดตั้ง Continue extension ใน VS Code

---

## 2026-06-01 — Phase A: Ollama + โมเดลหลัก ✅

- ติดตั้ง Ollama (official script, IPv4) — `/usr/local/bin/ollama`
- เปิด systemd service `ollama` (active, ฟังที่ `127.0.0.1:11434`)
- ดึงโมเดลชุดเริ่มต้น (decision #6):
  - `qwen2.5-coder:7b` — 4.7 GB (code-chat หลัก)
  - `qwen2.5-coder:3b` — 1.9 GB (autocomplete)
  - `qwen2.5:7b` — 4.7 GB (เขียน/แปล/คอนเทนต์)
- Verify ผ่าน: inference test (fizzbuzz Python) + แปลไทย ตอบถูกต้องทั้งคู่
- VRAM: 5031 MiB / 6144 MiB ขณะโหลด qwen2.5:7b — รัน sequential 1 โมเดลต่อครั้ง (Ollama จัดการเอง)
- Advisor ตรวจทาน: ✓ ทุกข้อ พร้อมไป Phase B

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
