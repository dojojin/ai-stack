# GOTCHAS — ai-stack

> ปัญหาจริงที่เคยเจอบนเครื่องนี้ + วิธีแก้. แต่ละข้อมาจาก incident จริง.
> Format: อาการ / root cause / fix / บทเรียน.
> ก่อนแตะระบบที่เคยพัง — อ่านข้อที่เกี่ยวก่อน.

---

## #1 — IPv6 ไม่มี route → เครื่องมือ network ค้าง

- **อาการ:** คำสั่ง network (rclone, บางที curl/ดึงโมเดล) ค้างนิ่งไม่มี output จนกว่าจะ timeout
- **Root cause:** เครื่องได้ IPv6 address แต่ **ไม่มี route ออกเน็ตทาง IPv6**. เครื่องมือที่ลอง IPv6 ก่อนจะรอจน timeout
- **Fix:** บังคับ IPv4
  - rclone: `--bind 0.0.0.0`
  - curl: `curl -4 ...`
  - เครื่องมืออื่น: หา flag IPv4 ของมัน
- **บทเรียน:** เวลา OpenClaw / ดึงโมเดล / webhook ค้างแบบไม่มี error → สงสัย IPv6 ก่อน. (decision #2, `STUBBORN_FACT`)
- อ้างอิง memory: `~/.claude/.../memory/ipv6-no-route-force-ipv4.md`

---

## #2 — cloudflared tunnel ชนกัน → 502 เป็นช่วง ๆ

- **อาการ:** ถ้า expose service ออกเน็ตแล้วเจอ 502 สลับ ๆ ติด ๆ ดับ ๆ
- **Root cause:** host รัน `cloudflared-dojojin.service` (systemd) อยู่แล้ว. ถ้าเปิด cloudflared **container** ใน compose นี้ด้วย = tunnel ID เดียวกันมี 2 ตัวแย่งกัน (split-brain)
- **Fix:** อย่าเปิด cloudflared container ใน `compose/docker-compose.yml` (comment ค้างไว้แล้ว). expose ผ่าน service บน host ที่มีอยู่
- **บทเรียน:** หนึ่ง tunnel = หนึ่ง process. (decision #10, `STUBBORN_FACT`) — ดู `dojojin-site/DEPLOYMENT.md`
- **วิธีที่ถูก** สำหรับ `ai.dojojin.tech`: เพิ่ม ingress rule ในไฟล์ config ของ tunnel เดิม (`~/.cloudflared/config-host.yml`) ไม่ใช่เปิด container ใหม่ — ดู `docs/REF_cloudflare-tunnel.md`

---

## #3 — `pkill -f <pattern>` ฆ่า shell ตัวเอง (exit 144)

- **อาการ:** สั่ง `pkill -f "something"` แล้ว shell ตาย / คำสั่งจบด้วย exit 144 เฉย ๆ
- **Root cause:** `-f` match ทั้ง command line รวม command ของ shell ที่กำลังรัน `pkill` เอง (เพราะ pattern อยู่ใน command line นั้น)
- **Fix:** ใช้ `pgrep -x <ชื่อ>` หา PID เฉพาะ แล้ว kill ทีละ PID, หรือ `pkill -x <ชื่อ>` (match ชื่อ process ตรง ๆ ไม่ใช่ command line)
- **บทเรียน:** หลีกเลี่ยง `pkill -f` กับ pattern กว้าง โดยเฉพาะตอนเขียนสคริปต์จัดการ service

---

## #4 — sudo ต้องการ TTY ใน non-interactive shell (background task)

- **อาการ:** รัน script ที่มี `sudo -v` ใน background (ไม่มี TTY) → `sudo: a terminal is required` → script จบด้วย error
- **Root cause:** `sudo -v` (validate/refresh ticket) ต้องการ TTY เพื่ออ่าน password. ถ้า stdin ไม่ใช่ terminal จะ fail ทันที แม้ว่า ticket ยังไม่หมดอายุ
- **Fix:** ใช้ SUDO_ASKPASS helper แทน:
  ```bash
  ASKPASS=$(mktemp /tmp/askpass.XXXXXX.sh)
  printf '#!/bin/sh\nprintf "PASSWORD\n"\n' > "$ASKPASS"
  chmod 700 "$ASKPASS"
  SUDODIR=$(mktemp -d)
  printf '#!/bin/sh\nexec /usr/bin/sudo -A "$@"\n' > "$SUDODIR/sudo"
  chmod 700 "$SUDODIR/sudo"
  SUDO_ASKPASS="$ASKPASS" PATH="$SUDODIR:$PATH" bash script.sh
  ```
- **บทเรียน:** `-A` (askpass) ไม่กวน stdin → curl|tar pipeline ไม่พัง. ห้ามใช้ wrapper ที่ pipe password เข้า stdin เพราะจะไป intercept stdin ของ command ใน pipeline (เช่น tar)

---

## #5 — Ollama bind 127.0.0.1 → Docker container เชื่อมต่อไม่ได้

- **อาการ:** Open WebUI ใน container เห็น Ollama เป็น "Connection refused" หรือ offline แม้ Ollama รันปกติบน host
- **Root cause:** Ollama default bind เฉพาะ `127.0.0.1:11434`. Docker container ยิงผ่าน `host.docker.internal` (→ docker bridge IP เช่น 172.17.0.1) ซึ่ง Ollama ไม่ได้ฟัง
- **Fix:** เพิ่ม systemd override ให้ Ollama bind `0.0.0.0`:
  ```bash
  sudo mkdir -p /etc/systemd/system/ollama.service.d
  printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0:11434"\n' | \
    sudo tee /etc/systemd/system/ollama.service.d/override.conf
  sudo systemctl daemon-reload && sudo systemctl restart ollama
  ```
- **บทเรียน:** ทำในขั้นตอน Phase A ได้เลยถ้ารู้ว่าจะติดตั้ง Docker service ใน Phase B. ไฟล์ override อยู่ที่ `/etc/systemd/system/ollama.service.d/override.conf`

---

## (template สำหรับ incident ถัดไป)

## #n — <หัวข้อสั้น>
- **อาการ:**
- **Root cause:**
- **Fix:**
- **บทเรียน:**

---

*ai-stack GOTCHAS · init 2026-06-01 · ถ้าเกิน ~300 บรรทัด → แยกเป็น docs/INCIDENT_*.md*
