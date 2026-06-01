# LOGIC_model-selection — ai-stack

> ตรรกะเลือกโมเดลตามงาน ภายใต้เพดาน **VRAM 6 GB** (RTX 3060 Laptop) + RAM 35 GB.
> โหลดเมื่อ: เลือก / เพิ่ม / เปลี่ยนโมเดล, ปรับ quant.
> กฎแข็ง: decision #5 (`STUBBORN_FACT`).

---

## เพดานฮาร์ดแวร์

| ทรัพยากร | ค่า | ความหมายต่อโมเดล |
|---|---|---|
| VRAM | **6 GB** | เพดานของ "fit GPU เต็ม" — โมเดล + context ต้องรวมไม่เกินนี้ถึงจะเร็ว |
| RAM | 35 GB | เผื่อ offload ส่วนเกินของโมเดลใหญ่ลงมา (ช้าลงมาก) |
| GPU | RTX 3060 Laptop | ~แรงพอสำหรับ 7–8B Q4 แบบ interactive |

**กฎ:** weights (Q4) + KV-cache(context) ≤ ~5.5 GB → ลื่น. เกินนั้น Ollama จะ offload layer ลง CPU/RAM อัตโนมัติ = ช้าลงตามสัดส่วนที่หลุดออกจาก GPU.

---

## ตารางเลือกโมเดลตามงาน

| งาน | โมเดล | ขนาด Q4 | ที่ตั้งบนเครื่องนี้ | ความเร็วคาดหวัง |
|---|---|---|---|---|
| **โค้ด-chat (หลัก)** | `qwen2.5-coder:7b` | ~4.7 GB | ✅ fit GPU เกือบเต็ม (ลด context ถ้าตึง) | ~25–40 tok/s |
| **autocomplete editor** | `qwen2.5-coder:3b` | ~2 GB | ✅ fit เต็ม เหลือเฟือ | ~50–70 tok/s |
| **เขียน/แปล/คอนเทนต์** | `qwen2.5:7b` | ~4.7 GB | ✅ fit GPU เกือบเต็ม | ~25–40 tok/s |
| **ภาษาดี ทางเลือก** | `gemma2:9b` | ~5.5 GB | ⚠️ ตึง — อาจ offload นิด | ~15–20 tok/s |
| **แปลไทย-อังกฤษเฉพาะทาง** | `chinda-mt` (ChindaMT-4B) | ~4 GB Q8 | ✅ ได้ (โมเดลแปลโดยเฉพาะ) | ดี |
| **คุณภาพสูง ยอมช้า** | `qwen2.5-coder:14b` | ~9 GB | ⚠️ offload ลง RAM หนัก | ~6–10 tok/s (ไม่ interactive) |
| **embedding (RAG)** | `nomic-embed-text` | ~0.3 GB | ✅ เล็กมาก | — |

**ห้าม:** โมเดล 27B+ (gemma2:27b, qwen2.5:32b ฯลฯ) แบบ interactive — offload เกินครึ่ง ช้าจนใช้งานจริงไม่ได้บน 6 GB. (decision #5)

---

## ทำไม Qwen2.5 เป็นค่าเริ่มต้น

- **qwen2.5-coder** = หนึ่งในโมเดลโค้ด open ที่ดีสุดในระดับ 7B (FIM/autocomplete + chat)
- ตระกูล Qwen2.5 **หลายภาษา** — ไทยใช้ได้ระดับโอเค (ไม่ใช่ดีสุด แต่พอสำหรับงานทั่วไป)
- มีหลายขนาด (1.5/3/7/14/32B) → สลับ autocomplete(3B) / chat(7B) ด้วยตระกูลเดียว สะดวก

> งานแปลไทยจริงจัง → ใช้ `chinda-mt` (เฉพาะทาง) แทน. งานเขียนไทยเชิงสร้างสรรค์ → ลอง `gemma2:9b` เทียบ.

---

## ปรับ context ถ้า VRAM ตึง

7B Q4 บน 6 GB: ถ้า OOM หรือ offload เยอะ → ลด `num_ctx`:
```bash
# ใน Modelfile หรือ runtime param
PARAMETER num_ctx 4096      # แทน 8192 — ประหยัด KV-cache
```
หรือเลือก quant เล็กลง (`q4_K_S` แทน `q4_K_M`) แลกคุณภาพนิดหน่อย.

---

## ขั้นตอนเพิ่มโมเดลใหม่ (เช็คลิสต์)

1. ประเมินขนาด Q4 vs 6 GB → fit เต็ม / ตึง / offload? (ใส่ในตารางด้านบน)
2. `ollama pull <model>` → `ollama run <model>` ทดสอบจริง
3. วัด tok/s + ดู `ollama ps` ว่า offload เท่าไหร่ (`100% GPU` = ดี)
4. ถ้ารับได้ → บันทึกเหตุผลใน [DECISIONS.md](../DECISIONS.md) + อัปเดตตารางนี้

---

*ai-stack · LOGIC_model-selection · init 2026-06-01*
