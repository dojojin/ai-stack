#!/usr/bin/env bash
# ai-stack — Phase C: OpenClaw (local brain, ปลอดภัยก่อน)
# ดู ROADMAP.md → Phase C
#
# หมายเหตุ: วิธีติดตั้ง OpenClaw เปลี่ยนได้ตามเวอร์ชัน — สคริปต์นี้ตั้งใจ "ไม่เดา"
# คำสั่งติดตั้ง. ยืนยันจาก docs ทางการก่อน (Investigate-first, Working Agreement #1):
#   https://docs.openclaw.ai/   ·   https://github.com/openclaw/openclaw
set -euo pipefail
source "$(dirname "$0")/lib.sh"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

log_step "Phase C — OpenClaw (local brain)"

# 0) prerequisite: Ollama จาก Phase A
ollama_up || die "Ollama ยังไม่ขึ้น — รัน Phase A ก่อน"
log_ok "Ollama พร้อม (provider ปลายทางของ OpenClaw)"

# 1) ติดตั้ง OpenClaw
if have_cmd openclaw; then
  log_ok "openclaw มีแล้ว: $(openclaw --version 2>/dev/null | head -1)"
else
  log_warn "ยังไม่มี openclaw — ยืนยันวิธีติดตั้งจาก docs ทางการก่อน (ไม่เดาในสคริปต์)"
  cat <<'EOF'

  ติดตั้งด้วยมือ (เลือกตามที่ docs ทางการระบุ ณ ตอนติดตั้ง):
    • Node/Bun:   ดู https://docs.openclaw.ai/  (เช่น npm i -g / bun add -g / curl installer)
    • Container:  ถ้ามี image ทางการ ให้เพิ่มเป็น service แยก
  ใช้ curl4 / -4 เสมอถ้าโหลดผ่านเน็ต (GOTCHAS #1: IPv6 ค้าง)

EOF
  die "หยุดก่อน install — ยืนยันคำสั่งทางการแล้วรันซ้ำ (idempotent: จะข้ามถ้ามี openclaw แล้ว)"
fi

# 2) ตั้งค่าให้ใช้ Ollama local เป็นสมอง + เปิดเฉพาะ local channel
#    (รายละเอียด config ขึ้นกับ schema ของ OpenClaw เวอร์ชันที่ลง — เติมหลังยืนยัน)
log_step "ค่าที่ต้องตั้ง (manual/config) — เน้นความปลอดภัย (decision #7, #8):"
cat <<EOF
  • provider/model → Ollama:  http://${OLLAMA_HOST_DEFAULT}  · model: qwen2.5:7b
  • channel:        เปิดเฉพาะ WebChat / local ก่อน — ยังไม่ต่อ LINE/Telegram (นั่นคือ Phase D)
  • permissions:    ปิด skill ที่รันเชลล์อันตราย/ลบไฟล์ จนกว่าจะมั่นใจ (allowlist เท่านั้น)
  • ห้าม:           เปิดช่องแชตสาธารณะแบบไม่มี allowlist (STUBBORN_FACT, governance)
EOF

# 3) Verify
echo
log_step "Verify (ทำเองหลัง config):"
cat <<EOF
  - เปิด WebChat ของ OpenClaw แล้วสั่งงานเบา ๆ ที่ตรวจผลได้ เช่น:
      "อ่านไฟล์ README.md แล้วสรุป 3 บรรทัด"
  - ยืนยันว่า traffic ไปที่ Ollama local (ดู: ollama ps ตอนสั่ง / nvidia-smi โหลดขึ้น)
  - ยืนยันว่ายัง 'ไม่มี' ช่องแชตภายนอกเปิดอยู่
EOF
log_ok "Phase C scaffold พร้อม — Phase D (cloud API + LINE/Telegram) ทำ manual ดู ROADMAP.md"
