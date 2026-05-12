import os
import base64
import json
from typing import Any, Dict, Optional, Tuple

def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    return v if v else default


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = text[start : end + 1]
    try:
        obj = json.loads(snippet)
        if isinstance(obj, dict):
            return obj
    except Exception:
        return None
    return None


def _normalize_item_payload(obj: Dict[str, Any]) -> Dict[str, Any]:
    def as_int(v: Any) -> Optional[int]:
        if v is None:
            return None
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        s = str(v).strip()
        if not s:
            return None
        digits = "".join(ch for ch in s if ch.isdigit() or ch == "-")
        if not digits or digits == "-":
            return None
        try:
            return int(digits)
        except Exception:
            return None

    def as_str(v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    out: Dict[str, Any] = {}
    out["name"] = as_str(obj.get("name"))
    out["description"] = as_str(obj.get("description"))
    out["quantity"] = as_int(obj.get("quantity")) or 0
    out["category"] = as_str(obj.get("category"))
    out["location"] = as_str(obj.get("location"))
    out["unit"] = as_str(obj.get("unit"))
    out["brand"] = as_str(obj.get("brand"))
    out["min_quantity"] = as_int(obj.get("min_quantity")) or 0
    out["purchase_date"] = as_str(obj.get("purchase_date"))
    out["expiry_date"] = as_str(obj.get("expiry_date"))
    out["barcode"] = as_str(obj.get("barcode"))
    out["tags"] = as_str(obj.get("tags"))
    out["notes"] = as_str(obj.get("notes"))
    return out


async def extract_item_from_image(
    image_bytes: bytes,
    filename: str,
    prompt_override: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    try:
        import httpx
    except Exception as e:
        raise RuntimeError("Missing dependency: httpx. Install it with: pip install httpx") from e

    model = _get_env("ARK_MODEL", "doubao-seed-2-0-code-preview-260215")
    base_url = _get_env("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    api_key = _get_env("ARK_API_KEY")
    if not api_key:
        raise RuntimeError("ARK_API_KEY is not set")

    env_prompt = _get_env("OCR_EXTRACT_PROMPT")
    prompt = (prompt_override or env_prompt or "").strip()
    if not prompt:
        prompt = (
            "你是OCR信息抽取助手。请从图片中提取家庭物品入库信息，输出严格JSON对象（不要markdown，不要多余文字）。"
            "字段：name,quantity,unit,category,location,min_quantity,purchase_date,expiry_date,brand,barcode,tags,notes,description。"
            "日期用YYYY-MM-DD，未知用null。quantity/min_quantity为整数。"
        )

    mime = "image/jpeg"
    lower = filename.lower()
    if lower.endswith(".png"):
        mime = "image/png"
    elif lower.endswith(".webp"):
        mime = "image/webp"

    b64 = base64.b64encode(image_bytes).decode("ascii")
    image_url = f"data:{mime};base64,{b64}"

    payload: Dict[str, Any] = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "你是一个严谨的结构化信息抽取助手。"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
    }

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=60.0, headers=headers) as client:
            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        try:
            body = e.response.text
        except Exception:
            body = ""
        body = (body or "").strip()
        if len(body) > 2000:
            body = body[:2000] + "..."
        raise RuntimeError(f"Ark returned {e.response.status_code}: {body or 'No response body'}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Ark request failed: {str(e)}") from e

    content = (
        (((data or {}).get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    )
    if not isinstance(content, str):
        content = str(content)
    obj = _extract_json_object(content)
    if obj is None:
        raise RuntimeError("Model output is not valid JSON")
    return _normalize_item_payload(obj), content

