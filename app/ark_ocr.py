import os
import base64
import json
from typing import Any, Dict, Optional, Tuple, List

def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    return v if v else default


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if "```" in text:
        start = text.find("```")
        end = text.find("```", start + 3)
        if end != -1:
            inner = text[start + 3 : end].strip()
            if inner.lower().startswith("json"):
                inner = inner[4:].strip()
            try:
                obj = json.loads(inner)
                if isinstance(obj, dict):
                    return obj
                if isinstance(obj, list) and obj and isinstance(obj[0], dict):
                    return obj[0]
            except Exception:
                pass
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            return obj[0]
    except Exception:
        pass
    s = text
    starts = [i for i, ch in enumerate(s) if ch == "{"][:200]
    for i in starts:
        depth = 0
        in_str = False
        esc = False
        quote = ""
        for j in range(i, min(len(s), i + 20000)):
            ch = s[j]
            if in_str:
                if esc:
                    esc = False
                    continue
                if ch == "\\":
                    esc = True
                    continue
                if ch == quote:
                    in_str = False
                    quote = ""
                continue
            else:
                if ch in ("'", '"'):
                    in_str = True
                    quote = ch
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        snippet = s[i : j + 1]
                        try:
                            obj = json.loads(snippet)
                            if isinstance(obj, dict):
                                return obj
                            if isinstance(obj, list) and obj and isinstance(obj[0], dict):
                                return obj[0]
                        except Exception:
                            break
        continue
    return None


def _normalize_item_payload(obj: Dict[str, Any]) -> Dict[str, Any]:
    def pick(*names: str) -> Any:
        for n in names:
            if n in obj and obj.get(n) is not None:
                return obj.get(n)
        return None

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
        if isinstance(v, list):
            parts = [str(x).strip() for x in v if str(x).strip()]
            s = ",".join(parts)
            return s if s else None
        s = str(v).strip()
        return s if s else None

    out: Dict[str, Any] = {}
    out["code"] = as_str(pick("code", "编码"))
    out["type_l1"] = as_str(pick("type_l1", "typeL1", "大类", "类型大类", "一级分类"))
    out["type_l2"] = as_str(pick("type_l2", "typeL2", "子类", "类型子类", "二级分类"))
    out["name"] = as_str(pick("name", "名称", "物品名称", "商品名称", "商品名"))
    out["description"] = as_str(pick("description", "描述", "说明"))
    out["usage"] = as_str(pick("usage", "用途", "使用场景"))
    out["image_path"] = as_str(pick("image_path", "image", "图片", "图片地址"))
    out["quantity"] = as_int(pick("quantity", "数量", "库存", "当前库存")) or 0
    out["category"] = as_str(pick("category", "分类", "品类"))
    out["location"] = as_str(pick("location", "位置", "存放位置", "存放", "地点"))
    out["room"] = as_str(pick("room", "房间", "区域"))
    out["spot"] = as_str(pick("spot", "具体位置", "位置细分", "墙面"))
    out["unit"] = as_str(pick("unit", "单位"))
    out["brand"] = as_str(pick("brand", "品牌"))
    out["min_quantity"] = as_int(pick("min_quantity", "最低库存", "最小库存", "补货线", "阈值")) or 0
    out["production_date"] = as_str(pick("production_date", "生产日期"))
    out["purchase_date"] = as_str(pick("purchase_date", "采购日期", "购买日期", "入库日期"))
    out["expiry_date"] = as_str(pick("expiry_date", "到期日", "保质期", "有效期", "过期日期"))
    out["barcode"] = as_str(pick("barcode", "条码", "条形码"))
    out["tags"] = as_str(pick("tags", "标签"))
    out["notes"] = as_str(pick("notes", "备注", "提示"))
    out["usage_status"] = as_str(pick("usage_status", "使用状态"))
    out["ownership"] = as_str(pick("ownership", "所有权"))
    out["price"] = pick("price", "价格", "购买价格")
    out["value_score"] = pick("value_score", "使用价值", "价值")
    out["replacement_cycle_days"] = as_int(pick("replacement_cycle_days", "建议更换周期", "更换周期", "更换周期天数"))
    out["usage_frequency"] = as_str(pick("usage_frequency", "使用频率"))
    out["related_item_ids"] = as_str(pick("related_item_ids", "关联物品"))
    out["responsible_person"] = as_str(pick("responsible_person", "责任人"))
    out["custom_json"] = pick("custom_json", "自定义属性", "其他属性")

    if not out.get("type_l1") and out.get("category"):
        out["type_l1"] = out.get("category")
    if not out.get("type_l2"):
        out["type_l2"] = None

    if out.get("custom_json") is not None and not isinstance(out.get("custom_json"), str):
        try:
            out["custom_json"] = json.dumps(out["custom_json"], ensure_ascii=False)
        except Exception:
            out["custom_json"] = None

    for k in ("price", "value_score"):
        v = out.get(k)
        if v is None or v == "":
            continue
        if isinstance(v, (int, float)):
            out[k] = float(v)
            continue
        s = str(v).strip()
        if not s:
            continue
        s2 = "".join(ch for ch in s if ch.isdigit() or ch in ".-")
        try:
            out[k] = float(s2)
        except Exception:
            out[k] = None
    return out


def _guess_mime(filename: str) -> str:
    lower = (filename or "").lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def _normalize_base_url(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return "https://ark.cn-beijing.volces.com/api/v3"
    s = s.rstrip("/")
    for suffix in ("/chat/completions", "/responses"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    return s


def _ark_config() -> Tuple[str, str, str]:
    model = _get_env("ARK_MODEL", "doubao-seed-2-0-lite-260428")
    base_url = _normalize_base_url(_get_env("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"))
    api_key = _get_env("ARK_API_KEY")
    if not api_key:
        raise RuntimeError("ARK_API_KEY is not set")
    return model, base_url, api_key


async def ark_chat(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    filename: str = "image.jpg",
    temperature: float = 0.2,
) -> Tuple[str, Dict[str, Any]]:
    try:
        import httpx
    except Exception as e:
        raise RuntimeError("Missing dependency: httpx. Install it with: pip install httpx") from e

    model, base_url, api_key = _ark_config()
    if not prompt or not prompt.strip():
        raise RuntimeError("Prompt is empty")

    content_blocks: List[Dict[str, Any]] = []
    if image_bytes is not None:
        mime = _guess_mime(filename)
        b64 = base64.b64encode(image_bytes).decode("ascii")
        content_blocks.append({"type": "input_image", "image_url": f"data:{mime};base64,{b64}"})
    content_blocks.append({"type": "input_text", "text": prompt.strip()})

    payload: Dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "input": [
            {
                "role": "user",
                "content": content_blocks,
            }
        ],
    }

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=60.0, headers=headers) as client:
            resp = await client.post("/responses", json=payload)
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

    text: Optional[str] = None
    output = (data or {}).get("output")
    if isinstance(output, list) and output:
        parts: List[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            blocks = item.get("content")
            if not isinstance(blocks, list):
                continue
            for b in blocks:
                if not isinstance(b, dict):
                    continue
                t = b.get("type")
                if t in ("output_text", "text") and isinstance(b.get("text"), str):
                    parts.append(b["text"])
        if parts:
            text = "\n".join(parts).strip()
    if not text:
        text = (data or {}).get("output_text")
    if not isinstance(text, str) or not text.strip():
        text = json.dumps(data, ensure_ascii=False)
    return text, data


async def extract_item_from_image(
    image_bytes: bytes,
    filename: str,
    prompt_override: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    env_prompt = _get_env("OCR_EXTRACT_PROMPT")
    base_prompt = (env_prompt or "").strip()
    if not base_prompt:
        base_prompt = (
            "你是OCR信息抽取助手。请从图片中提取家庭物品入库信息，输出严格JSON对象（不要markdown，不要多余文字）。"
            "字段："
            "type_l1,type_l2,name,usage,quantity,unit,"
            "production_date,purchase_date,expiry_date,"
            "room,spot,location,"
            "usage_status,ownership,"
            "price,value_score,replacement_cycle_days,"
            "usage_frequency,responsible_person,"
            "brand,barcode,tags,notes,description。"
            "日期用YYYY-MM-DD，未知用null。quantity/min_quantity/replacement_cycle_days为整数。"
        )
    user_prompt = (prompt_override or "").strip()
    if user_prompt:
        prompt = f"{base_prompt}\n\n用户补充要求：{user_prompt}"
    else:
        prompt = base_prompt

    content, _raw_json = await ark_chat(prompt=prompt, image_bytes=image_bytes, filename=filename, temperature=0.0)
    obj = _extract_json_object(content)
    if obj is None:
        excerpt = content.strip()
        if len(excerpt) > 1800:
            excerpt = excerpt[:1800] + "..."
        repair_prompt = (
            "你刚才的输出不是严格JSON。请将下面内容转换为严格JSON对象（不要markdown，不要多余文字）。"
            "必须只输出一个JSON对象，字段为："
            "type_l1,type_l2,name,usage,quantity,unit,"
            "production_date,purchase_date,expiry_date,"
            "room,spot,location,"
            "usage_status,ownership,"
            "price,value_score,replacement_cycle_days,"
            "usage_frequency,responsible_person,"
            "brand,barcode,tags,notes,description。"
            "日期用YYYY-MM-DD，未知用null。quantity/replacement_cycle_days为整数。"
            f"\n\n待转换内容：\n{excerpt}"
        )
        repaired, _raw2 = await ark_chat(prompt=repair_prompt, image_bytes=None, filename="text.txt", temperature=0.0)
        obj = _extract_json_object(repaired)
        if obj is None:
            excerpt2 = repaired.strip()
            if len(excerpt2) > 1200:
                excerpt2 = excerpt2[:1200] + "..."
            raise RuntimeError(f"Model output is not valid JSON. content_excerpt={excerpt2}")
        return _normalize_item_payload(obj), content
    return _normalize_item_payload(obj), content

