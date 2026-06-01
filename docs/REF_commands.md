# REF_commands — ai-stack

> คำสั่ง ops ประจำวัน. lookup อย่างเดียว — เหตุผล/ตรรกะอยู่ในไฟล์ LOGIC/ARCH.

---

## Ollama

```bash
ollama list                          # โมเดลที่มี
ollama ps                            # โมเดลที่โหลดอยู่ + GPU/CPU split
ollama run qwen2.5-coder:7b "..."    # แชตเร็ว ๆ จาก CLI
ollama pull <model>                  # ดึงโมเดล (ถ้าค้าง → สงสัย IPv6, GOTCHAS #1)
ollama rm <model>                    # ลบโมเดล
ollama create chinda-mt -f models/ChindaMT-4B.Modelfile   # สร้างจาก Modelfile

# service (host systemd)
sudo systemctl status ollama
sudo systemctl restart ollama
journalctl -u ollama -f              # ดู log (หา 'library=cuda' = เห็น GPU)
```

## Open WebUI (docker compose)

```bash
cd compose
docker compose up -d                 # เปิด
docker compose ps                    # สถานะ
docker compose logs -f openwebui     # log
docker compose down                  # ปิด
docker compose pull && docker compose up -d   # อัปเดต
# เข้าใช้: http://localhost:3000
```

## Continue.dev

```bash
# config อยู่ที่:
~/.continue/config.json
# แก้แล้ว reload: VS Code Command Palette → "Continue: Reload"
```

## OpenClaw (เฟส C ขึ้นไป)

```bash
# (เติมคำสั่งจริงหลังติดตั้งเฟส C)
# ตรวจ provider ชี้ Ollama: 127.0.0.1:11434
# ดู log / ช่องแชตที่เปิด / allowlist
```

## GPU / ระบบ

```bash
nvidia-smi                           # VRAM/อุณหภูมิ/โหลด
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
watch -n1 nvidia-smi                 # ดูสด ๆ ตอนรันโมเดล
free -h                              # RAM
df -h /                              # ดิสก์ (โมเดลกินเยอะ)
```

## เน็ต (บังคับ IPv4 — GOTCHAS #1)

```bash
curl -4 -fsS <url>                   # บังคับ IPv4
# rclone: --bind 0.0.0.0
```

---

*ai-stack · REF_commands · init 2026-06-01*
