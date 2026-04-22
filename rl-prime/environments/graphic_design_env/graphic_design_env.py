import base64
import csv
import json
import re
import uuid
from pathlib import Path
from typing import Any

import verifiers as vf
from datasets import Dataset
from verifiers.types import ClientConfig
from verifiers.utils.client_utils import setup_anthropic_client, setup_openai_client

from prompts import EDIT_CRITIC_PROMPT, POLICY_INSTRUCTIONS


DATA_DIR = Path(__file__).parent / "data"
ORIGINALS_DIR = DATA_DIR / "original"
EDITS_CSV = Path(__file__).parent / "edits.csv"
EDITS_OUTPUT_DIR = Path(__file__).parent / "outputs" / "edits"


def _media_type(path: Path) -> str:
    ext = path.suffix.lstrip(".").lower()
    return "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"


def _image_to_data_url(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{_media_type(path)};base64,{b64}"


def _image_to_anthropic_block(path: Path) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": _media_type(path),
            "data": base64.b64encode(path.read_bytes()).decode(),
        },
    }


def _b64_to_anthropic_block(b64_data: str, media_type: str = "image/png") -> dict:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": b64_data},
    }


def _resolve_image_path(template_id: str) -> Path | None:
    for ext in ("webp", "jpg", "jpeg", "png"):
        p = ORIGINALS_DIR / f"{template_id}.{ext}"
        if p.exists():
            return p
    return None


def _parse_score(text: str) -> float:
    m = re.search(r"SCORE:\s*(\d+)", text)
    return float(m.group(1)) / 100.0 if m else 0.0


def _strip_nulls(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_nulls(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_nulls(x) for x in obj]
    return obj


class _MultimodalSingleTurnEnv(vf.SingleTurnEnv):
    """SingleTurnEnv that strips null fields from multimodal prompts.

    Why: HF Datasets unifies the struct schema across mixed content-part types,
    so image parts gain a `text: None` key and vice versa. OpenAI rejects those
    as unexpected. Clean them up before the prompt leaves the env.
    """

    async def setup_state(self, state):
        prompt = state.get("prompt")
        if isinstance(prompt, list):
            cleaned = []
            for msg in prompt:
                if hasattr(msg, "model_dump"):
                    msg = msg.model_dump(exclude_none=True)
                cleaned.append(_strip_nulls(msg))
            state["prompt"] = cleaned
        return state


def _build_dataset(csv_path: Path, max_examples: int | None) -> Dataset:
    rows: list[dict] = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            image_path = _resolve_image_path(row["template_id"])
            if image_path is None:
                continue
            rows.append({
                "prompt": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url",
                         "image_url": {"url": _image_to_data_url(image_path)}},
                        {"type": "text",
                         "text": f"{POLICY_INSTRUCTIONS}\n\nEdit instruction: {row['instruction']}"},
                    ],
                }],
                "answer": row["instruction"],
                "info": {
                    "template_id": row["template_id"],
                    "image_path": str(image_path),
                    "edit_type": row["edit_type"],
                    "categories": row["categories"],
                },
            })
            if max_examples is not None and len(rows) >= max_examples:
                break
    return Dataset.from_list(rows)


def load_environment(
    edits_csv: str | None = None,
    max_examples: int = -1,
    judge_base_url: str = "https://api.anthropic.com",
    judge_api_key_var: str = "ANTHROPIC_API_KEY",
    judge_model: str = "claude-sonnet-4-6",
    judge_max_tokens: int = 1024,
    judge_sampling_args: dict[str, Any] | None = None,
    editor_base_url: str = "https://api.openai.com/v1",
    editor_api_key_var: str = "OPENAI_API_KEY",
    editor_model: str = "gpt-image-1",
    editor_size: str = "1024x1024",
    **kwargs: Any,
) -> vf.Environment:
    csv_path = Path(edits_csv) if edits_csv else EDITS_CSV
    limit = None if max_examples < 0 else max_examples
    dataset = _build_dataset(csv_path, max_examples=limit)
    EDITS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    judge_client = setup_anthropic_client(ClientConfig(
        api_base_url=judge_base_url,
        api_key_var=judge_api_key_var,
    ))
    editor_client = setup_openai_client(ClientConfig(
        api_base_url=editor_base_url,
        api_key_var=editor_api_key_var,
    ))

    async def edit_faithfulness(completion, answer, info, **_) -> float:
        if isinstance(completion, list):
            if not completion:
                return 0.0
            refined_prompt = completion[-1].get("content") or ""
        else:
            refined_prompt = str(completion or "")
        if not refined_prompt.strip():
            return 0.0
        orig_path = Path(info["image_path"])

        with orig_path.open("rb") as img_file:
            edit_resp = await editor_client.images.edit(
                model=editor_model,
                image=img_file,
                prompt=refined_prompt,
                size=editor_size,
            )
        edited_b64 = edit_resp.data[0].b64_json
        uid = uuid.uuid4().hex[:8]
        stem = f"{info['template_id']}__{uid}"
        (EDITS_OUTPUT_DIR / f"{stem}.png").write_bytes(
            base64.b64decode(edited_b64)
        )

        sampling = {"max_tokens": judge_max_tokens, **(judge_sampling_args or {})}
        judge_resp = await judge_client.messages.create(
            model=judge_model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": EDIT_CRITIC_PROMPT},
                    {"type": "text", "text": "Original image:"},
                    _image_to_anthropic_block(orig_path),
                    {"type": "text", "text": "Edited image:"},
                    _b64_to_anthropic_block(edited_b64),
                    {"type": "text", "text": f"Edit instruction: {answer}"},
                ],
            }],
            **sampling,
        )
        judge_text = "".join(b.text for b in judge_resp.content if b.type == "text")
        score = _parse_score(judge_text)
        (EDITS_OUTPUT_DIR / f"{stem}.json").write_text(json.dumps({
            "template_id": info["template_id"],
            "edit_type": info["edit_type"],
            "categories": info["categories"],
            "original_image": info["image_path"],
            "instruction": answer,
            "refined_prompt": refined_prompt,
            "score": score,
            "judge_response": judge_text,
        }, indent=2))
        return score

    rubric = vf.Rubric(funcs=[edit_faithfulness])
    return _MultimodalSingleTurnEnv(dataset=dataset, rubric=rubric)
