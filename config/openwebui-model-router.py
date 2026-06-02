"""
title: Model Router (ai-stack)
author: dojojin
version: 1.0.0
description: >
  Auto-route คำถามไปยังโมเดลที่เหมาะสมอัตโนมัติ:
  - มีรูปภาพ       → gemma3:4b       (multimodal)
  - โค้ด / debug   → qwen2.5-coder:7b (code specialist)
  - ทั่วไป / ไทย   → qwen2.5:7b      (general)
"""

import re
import json
import requests
from typing import Generator, Iterator
from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = Field(
            default="http://host.docker.internal:11434",
            description="Ollama API URL (จาก container → host)"
        )
        SHOW_ROUTING_REASON: bool = Field(
            default=True,
            description="แสดงเหตุผลที่เลือกโมเดลนี้ก่อนตอบ"
        )

    def __init__(self):
        self.type = "pipe"
        self.name = "🔀 Model Router"
        self.valves = self.Valves()

    def _detect_model(self, messages: list) -> tuple[str, str]:
        """
        วิเคราะห์ messages แล้วเลือกโมเดลที่เหมาะสม
        return: (model_name, reason)
        """
        last_msg = messages[-1] if messages else {}
        content = last_msg.get("content", "")

        # --- ตรวจรูปภาพ ---
        if isinstance(content, list):
            has_image = any(
                isinstance(c, dict) and c.get("type") == "image_url"
                for c in content
            )
            if has_image:
                return "gemma3:4b", "🖼️ ตรวจพบรูปภาพ → gemma3:4b (multimodal)"
            # รวม text parts
            text = " ".join(
                c.get("text", "") for c in content
                if isinstance(c, dict) and c.get("type") == "text"
            )
        else:
            text = content

        # --- ตรวจโค้ด (keyword + regex) ---
        CODE_PATTERNS = [
            # syntax markers
            r"```",
            r"\bdef\s+\w+\s*\(",
            r"\bclass\s+\w+",
            r"\bimport\s+\w+",
            r"\bfunction\s*\(",
            r"\bconst\s+\w+\s*=",
            r"\bvar\s+\w+",
            r"\blet\s+\w+",
            # thai code keywords
            r"โค้ด", r"สคริปต์", r"ฟังก์ชัน", r"โปรแกรม",
            r"บัค", r"เออเรอร์", r"debug",
            # common code terms
            r"\berror\b", r"\bbug\b", r"\bfix\b",
            r"\bapi\b", r"\bjson\b", r"\bsql\b",
            r"\bbash\b", r"\bshell\b", r"\bpython\b",
            r"\bjavascript\b", r"\btypescript\b",
        ]

        if any(re.search(p, text, re.IGNORECASE) for p in CODE_PATTERNS):
            return "qwen2.5-coder:7b", "💻 ตรวจพบคำถามเกี่ยวกับโค้ด → qwen2.5-coder:7b"

        # --- default: general / Thai ---
        return "qwen2.5:7b", "💬 คำถามทั่วไป → qwen2.5:7b"

    def pipe(self, body: dict) -> Generator:
        messages = body.get("messages", [])
        model, reason = self._detect_model(messages)

        # แสดงเหตุผลก่อนตอบ (ถ้าเปิด)
        if self.valves.SHOW_ROUTING_REASON:
            yield f"*{reason}*\n\n"

        # ส่งต่อไป Ollama
        payload = {**body, "model": model, "stream": True}

        try:
            resp = requests.post(
                f"{self.valves.OLLAMA_BASE_URL}/api/chat",
                json=payload,
                stream=True,
                timeout=120,
            )
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

        except requests.exceptions.RequestException as e:
            yield f"\n\n❌ Router error: {e}\nลองเลือกโมเดลตรง ๆ แทน"
