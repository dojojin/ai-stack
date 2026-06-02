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

## #6 — `openclaw onboard --non-interactive` flag ไม่รู้จัก

- **อาการ:** รัน `openclaw onboard --install-daemon --non-interactive` แล้วได้ error flag unknown → script หยุด
- **Root cause:** OpenClaw เวอร์ชันใหม่เปลี่ยน onboard flow — `--non-interactive` ไม่ใช่ flag ที่รองรับ
- **Fix:** แยกขั้นตอนออก:
  ```bash
  npm install -g openclaw@latest   # install binary
  # ข้าม onboard — วาง config ด้วยมือแทน (~/.openclaw/openclaw.json)
  openclaw gateway install         # ติดตั้ง systemd user service
  openclaw gateway start           # เริ่ม service
  loginctl enable-linger <user>    # ให้ service รอดหลัง logout (ต้อง sudo)
  ```
- **บทเรียน:** อย่า assume flag ของ onboard — วาง config ด้วยมือดีกว่าและ idempotent กว่า

---

## #7 — OpenClaw memorySearch default เป็น OpenAI → gateway ไม่สมบูรณ์

- **อาการ:** `openclaw doctor` รายงาน "Memory search provider is set to openai but no API key was found" ทั้งที่ตั้งใจใช้ Ollama อย่างเดียว
- **Root cause:** OpenClaw ค่า default ของ `agents.defaults.memorySearch.enabled` = true และชี้ไป OpenAI embedding — ถ้าไม่มี key จะ warn แต่ยังรันต่อ
- **Fix:** ปิดทันทีหลังติดตั้ง:
  ```bash
  openclaw config set agents.defaults.memorySearch.enabled false
  systemctl --user restart openclaw-gateway
  ```
- **บทเรียน:** ทำใน phase-c script ก่อน start gateway ครั้งแรก

---

## #8 — `openclaw gateway` ไม่ติดตั้ง daemon โดยอัตโนมัติ

- **อาการ:** หลัง `npm install -g openclaw` แล้ว gateway ไม่รัน — `openclaw doctor` รายงาน "Gateway service not installed"
- **Root cause:** installation ผ่าน npm ไม่ได้ auto-install systemd service — ต้องทำแยก
- **Fix (ลำดับถูกต้อง):**
  ```bash
  openclaw gateway install                    # สร้าง ~/.config/systemd/user/openclaw-gateway.service
  sudo loginctl enable-linger <username>      # ให้ user service รอดหลัง logout
  openclaw gateway start                      # start + enable
  systemctl --user is-active openclaw-gateway # ยืนยัน
  ```
- **บทเรียน:** ทำ linger ก่อน start เสมอ ไม่งั้น gateway ดับเมื่อ idle session timeout

---

## #9 — `commands.ownerAllowFrom` format ต้องเป็น JSON array ของ channel ID

- **อาการ:** `openclaw config set commands.ownerAllowFrom "local"` → "Config validation failed: Invalid input"
- **Root cause:** field นี้รับ array ของ channel-prefixed ID เท่านั้น เช่น `["telegram:123456789"]`
- **Fix (Phase D):** ตั้งเมื่อมี channel ID จริง:
  ```bash
  openclaw config set commands.ownerAllowFrom '["telegram:YOUR_ID"]'
  systemctl --user restart openclaw-gateway
  ```
- **บทเรียน:** ข้ามไปก่อนได้ถ้ายังไม่ต่อ external channel — doctor จะ warn แต่ไม่ block

---

## #10 — Open WebUI `ENABLE_SIGNUP=false` บล็อก admin คนแรกด้วย

- **อาการ:** กด Create Admin Account แล้วได้ error "You do not have permission" ทั้งที่ยังไม่มี user เลย — log แสดง `POST /api/v1/auths/signup HTTP/1.1" 403`
- **Root cause:** `ENABLE_SIGNUP=false` ใน docker-compose.yml บล็อก `/api/v1/auths/signup` ทุก request รวมถึง admin คนแรกด้วย (Open WebUI เวอร์ชันใหม่ไม่ยกเว้น first-user)
- **Fix:** เปิด signup ชั่วคราว → สร้าง admin → ปิดคืน:
  ```bash
  # แก้ compose/docker-compose.yml: ENABLE_SIGNUP=true
  docker compose -f compose/docker-compose.yml up -d
  # สมัคร admin ที่ http://localhost:3000
  # แก้กลับ: ENABLE_SIGNUP=false
  docker compose -f compose/docker-compose.yml up -d
  ```
- **บทเรียน:** ตั้ง `ENABLE_SIGNUP=false` หลังสมัคร admin เสร็จแล้วเท่านั้น ไม่ใช่ตั้งแต่แรก

---

## #11 — `op signin` ต้องการ TTY → ไม่ทำงานใน non-interactive shell

- **อาการ:** `eval $(op signin)` หรือ `op signin` ใน script/pipe → `[ERROR] inappropriate ioctl for device`
- **Root cause:** `op signin` ต้องอ่าน master password จาก TTY — ถ้าไม่มี terminal จริงจะ fail
- **Fix:** รันใน terminal จริงเท่านั้น (Konsole, iTerm, Windows Terminal) ไม่ใช่ผ่าน Claude Code หรือ CI
- **บทเรียน:** เขียน script แยก → ให้รันใน Konsole แทนการรันผ่าน Claude Code

---

## #12 — vault "Private" ไม่มีใน 1Password → ต้องตรวจชื่อก่อน

- **อาการ:** `op item create --vault=Private` → `"Private" isn't a vault in this account`
- **Root cause:** vault default บัญชีนี้ชื่อ **Personal** ไม่ใช่ Private
- **Fix:** ตรวจชื่อ vault จริงก่อนเสมอ: `op vault list` → ใช้ชื่อจาก NAME column
- **บทเรียน:** อย่า assume ชื่อ vault — ตรวจก่อนทุกครั้ง

---

## #13 — `op item create --category="SSH Key"` ไม่รับ field "private key" ตรง ๆ

- **อาการ:** `"private key[concealed]=..."` → `cannot assign the reserved field "private key"`
- **Root cause:** category SSH Key มี reserved fields ที่ต้องใช้ syntax พิเศษ
- **Fix:** เก็บ SSH key เป็น **Document** แทน (`op document create`) — restore ได้ถูกต้องกว่าด้วย
  ```bash
  op document create ~/.ssh/id_ed25519 --title="..." --vault=Personal
  op document get "..." > ~/.ssh/id_ed25519 && chmod 600 ~/.ssh/id_ed25519
  ```
- **บทเรียน:** files (SSH key, credentials JSON) → `op document create` / text tokens → `op item create`

---

## #14 — Windows SSH config อ่านถูกแต่ Host name ไม่ตรง → resolve ล้มเหลว

- **อาการ:** `ssh ai-stack` → `Could not resolve hostname ai-stack` แม้ config ถูกต้อง
- **Root cause:** ไฟล์ `~/.ssh/config` มี `Host dojojin` ไม่ใช่ `Host ai-stack` — ชื่อ Host ไม่ match
- **Fix:** ตรวจ config ด้วย `Get-Content "$env:USERPROFILE\.ssh\config"` ก่อน ssh ทุกครั้ง
  หรือ recreate ด้วย PowerShell:
  ```powershell
  @"
  Host ai-stack
      HostName ssh.dojojin.tech
      User kiseki
      ProxyCommand cloudflared access ssh --hostname %h
  "@ | Out-File -FilePath "$env:USERPROFILE\.ssh\config" -Encoding ascii -Force
  ```
- **บทเรียน:** Windows SSH config encoding ผิด (BOM/CRLF) → ใช้ `Out-File -Encoding ascii` เสมอ

---

## (template สำหรับ incident ถัดไป)

## #n — <หัวข้อสั้น>
- **อาการ:**
- **Root cause:**
- **Fix:**
- **บทเรียน:**

---

*ai-stack GOTCHAS · init 2026-06-01 · ถ้าเกิน ~300 บรรทัด → แยกเป็น docs/INCIDENT_*.md*
