#!/usr/bin/env python3
"""Execute a prepared image job using an externally configured image API."""

import argparse
import base64
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image


ADAPTERS = {"openrouter_images", "openai_images"}
CONFIG_ENV = {
    "adapter": "IMAGE_API_ADAPTER", "base_url": "IMAGE_API_BASE_URL",
    "model": "IMAGE_MODEL", "api_key_env": "IMAGE_API_KEY_ENV",
    "auth": "IMAGE_API_AUTH", "auth_header": "IMAGE_API_AUTH_HEADER",
    "auth_prefix": "IMAGE_API_AUTH_PREFIX", "timeout": "IMAGE_API_TIMEOUT",
}
SECRET_FIELDS = {"api_key", "apikey", "x-api-key", "api_token", "token", "authorization", "password", "access_token", "secret"}
RESERVED = {"model", "prompt", "image", "images", "input_references"}


class JobError(Exception):
    pass


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise JobError(f"不能读取 JSON 文件：{path}（{type(error).__name__}）") from error
    if not isinstance(data, dict):
        raise JobError(f"JSON 顶层必须是对象：{path}")
    return data


def validate_url(url, *, api=False):
    if not isinstance(url, str) or re.search(r"[\s\x00-\x1f]", url):
        raise JobError("API 或图片地址格式不合法")
    parsed = urlsplit(url)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise JobError("地址必须包含主机名，凭据应通过环境变量提供")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
        raise JobError("远程地址必须使用 HTTPS；本地服务可使用 HTTP")
    if parsed.fragment or (api and parsed.query):
        raise JobError("API 根地址不能带查询参数或片段；密钥使用请求头传递")
    return url.rstrip("/") if api else url


def reject_secrets(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in SECRET_FIELDS:
                raise JobError("任务和请求参数不能包含密钥；使用密钥环境变量")
            reject_secrets(child)
    elif isinstance(value, list):
        for child in value:
            reject_secrets(child)


def connection(args, env):
    config_path = args.config or env.get("IMAGE_CONFIG_FILE")
    config = read_json(Path(config_path).expanduser()) if config_path else {}
    allowed = set(CONFIG_ENV) | {"request_defaults"}
    if set(config) - allowed:
        raise JobError("外部配置含未知字段：" + ", ".join(sorted(set(config) - allowed)))
    for key, variable in CONFIG_ENV.items():
        if variable in env:
            config[key] = env[variable]
    for key in ("adapter", "base_url", "model"):
        if getattr(args, key) is not None:
            config[key] = getattr(args, key)
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise JobError(f"缺少配置 {CONFIG_ENV[key]}；未选择默认模型、地址或接口")
        config[key] = config[key].strip()
    if config["adapter"] not in ADAPTERS:
        raise JobError("不支持的接口类型；可选：" + ", ".join(sorted(ADAPTERS)))
    config["base_url"] = validate_url(config["base_url"], api=True)
    defaults = config.get("request_defaults", {})
    if "IMAGE_API_PARAMS" in env:
        try:
            overrides = json.loads(env["IMAGE_API_PARAMS"])
        except ValueError as error:
            raise JobError("IMAGE_API_PARAMS 必须是 JSON 对象") from error
        if not isinstance(defaults, dict) or not isinstance(overrides, dict):
            raise JobError("request_defaults 和 IMAGE_API_PARAMS 必须是对象")
        defaults = {**defaults, **overrides}
    if not isinstance(defaults, dict):
        raise JobError("request_defaults 必须是对象")
    config["request_defaults"] = defaults
    config.setdefault("api_key_env", "IMAGE_API_KEY")
    config.setdefault("auth", "key")
    config.setdefault("auth_header", "Authorization")
    config.setdefault("auth_prefix", "Bearer ")
    if config["auth"] not in ("key", "none"):
        raise JobError("auth 只能是 key 或 none")
    if not isinstance(config["api_key_env"], str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", config["api_key_env"]):
        raise JobError("api_key_env 必须是环境变量名")
    if not isinstance(config["auth_header"], str) or not re.fullmatch(r"[A-Za-z0-9-]+", config["auth_header"]):
        raise JobError("auth_header 必须是请求头名称")
    if not isinstance(config["auth_prefix"], str) or re.search(r"[\r\n]", config["auth_prefix"]):
        raise JobError("auth_prefix 不能包含换行")
    try:
        config["timeout"] = float(config.get("timeout", 180))
    except (TypeError, ValueError) as error:
        raise JobError("timeout 必须为正数秒数") from error
    if not math.isfinite(config["timeout"]) or config["timeout"] <= 0:
        raise JobError("timeout 必须为正数秒数")
    return config


def inspect_image(blob, *, alpha=False):
    try:
        with Image.open(io.BytesIO(blob)) as image:
            info = {"format": image.format, "width": image.width, "height": image.height}
            image.verify()
        if info["format"] not in {"PNG", "JPEG", "WEBP"}:
            raise JobError("第一版仅保存 PNG、JPEG、WebP 栅格图像")
        if alpha:
            with Image.open(io.BytesIO(blob)) as image:
                info["has_alpha"] = "A" in image.getbands() or "transparency" in image.info
                if info["has_alpha"]:
                    low, high = image.convert("RGBA").getchannel("A").getextrema()
                    info["contains_transparency"] = low < 255
                    info["contains_visible_pixels"] = high > 0
        return {**info, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
    except (OSError, ValueError, SyntaxError) as error:
        raise JobError("返回或参考文件不是可解码的有效图片") from error


def prepare(job_path, config):
    job = read_json(job_path)
    reject_secrets(job)
    allowed = {"mode", "prompt", "style", "format", "references", "parameters", "user_request"}
    if set(job) - allowed:
        raise JobError("任务含未知字段：" + ", ".join(sorted(set(job) - allowed)))
    if job.get("mode", "generate") not in {"generate", "edit"}:
        raise JobError("mode 只能是 generate 或 edit")
    if not isinstance(job.get("prompt"), str) or not job["prompt"].strip():
        raise JobError("任务必须包含完整 prompt")
    if not isinstance(job.get("style", {}), dict):
        raise JobError("style 必须是用于留档的对象")
    if not isinstance(job.get("format", {}), dict):
        raise JobError("format 必须是用于留档的对象")
    supplied = job.get("parameters", {})
    if not isinstance(supplied, dict):
        raise JobError("parameters 必须是对象")
    parameters = {**config["request_defaults"], **supplied}
    reject_secrets(parameters)
    if RESERVED & parameters.keys():
        raise JobError("模型由连接配置选择；prompt 和参考图由任务字段提供，不能在 parameters 中覆盖")
    if parameters.get("stream") not in (None, False):
        raise JobError("第一版使用同步响应，不支持 stream=true")
    parameters.pop("stream", None)
    if "output_format" in parameters and parameters["output_format"] not in ("png", "jpeg", "webp"):
        raise JobError("第一版 output_format 支持 png、jpeg、webp")
    if "background" in parameters and parameters["background"] not in ("auto", "opaque", "transparent"):
        raise JobError("background 必须是 auto、opaque 或 transparent")
    count = parameters.setdefault("n", 1)
    if type(count) is not int or not 1 <= count <= 10:
        raise JobError("n 必须是 1—10 的整数")
    if parameters.get("background") == "transparent" and parameters.get("output_format") not in (None, "png", "webp"):
        raise JobError("透明底需要 PNG 或 WebP，不能使用 JPEG")
    raw_refs = job.get("references", [])
    if not isinstance(raw_refs, list):
        raise JobError("references 必须是数组")
    if job.get("mode") == "edit" and not raw_refs:
        raise JobError("编辑任务必须提供实际修改目标")
    refs = []
    for reference in raw_refs:
        if not isinstance(reference, dict) or set(reference) != {"path", "role"}:
            raise JobError("每张参考图必须提供 path 和 role")
        if not all(isinstance(reference[key], str) and reference[key].strip() for key in ("path", "role")):
            raise JobError("参考图路径与用途不能为空")
        path = Path(reference["path"]).expanduser()
        path = (job_path.parent / path).resolve() if not path.is_absolute() else path.resolve()
        if not path.is_file() or path.stat().st_size > 50 * 1024 * 1024:
            raise JobError(f"参考文件不存在或大于 50MB：{path}")
        blob = path.read_bytes()
        info = inspect_image(blob)
        mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}[info["format"]]
        refs.append({"path": str(path), "role": reference["role"], "mime_type": mime, **info, "blob": blob})
    prompt = job["prompt"].strip()
    if refs:
        prompt += "\n\n输入图用途（与实际输入顺序一致）：\n" + "\n".join(f"图 {i + 1}：{ref['role']}" for i, ref in enumerate(refs))
    return job, prompt, parameters, refs


def multipart(fields, refs):
    boundary = "imagejob-" + uuid.uuid4().hex
    chunks = []
    for key, value in fields.items():
        if not re.fullmatch(r"[A-Za-z0-9_\[\]-]+", key):
            raise JobError("multipart 参数名含不支持的字符")
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, allow_nan=False)
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{text}\r\n'.encode())
    for i, ref in enumerate(refs):
        extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[ref["mime_type"]]
        chunks.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; filename="reference-{i + 1}.{extension}"\r\nContent-Type: {ref["mime_type"]}\r\n\r\n'.encode(), ref["blob"], b"\r\n"])
    chunks.append(f"--{boundary}--\r\n".encode())
    return f"multipart/form-data; boundary={boundary}", b"".join(chunks)


def request(config, prompt, parameters, refs):
    fields = {"model": config["model"], "prompt": prompt, **parameters}
    if config["adapter"] == "openrouter_images":
        fields.setdefault("response_format", "b64_json")
        if refs:
            fields["input_references"] = [{"type": "image_url", "image_url": {"url": "data:" + ref["mime_type"] + ";base64," + base64.b64encode(ref["blob"]).decode("ascii")}} for ref in refs]
        return config["base_url"] + "/images", "application/json", json.dumps(fields, ensure_ascii=False, allow_nan=False).encode()
    if refs:
        content_type, body = multipart(fields, refs)
        return config["base_url"] + "/images/edits", content_type, body
    return config["base_url"] + "/images/generations", "application/json", json.dumps(fields, ensure_ascii=False, allow_nan=False).encode()


def http(url, headers, body, timeout):
    validate_url(url)
    with tempfile.TemporaryDirectory(prefix="image-request-") as directory:
        directory = Path(directory)
        response_path = directory / "response"
        command = ["curl", "--silent", "--show-error", "--connect-timeout", "20", "--max-time", str(timeout), "--header", "@-", "--output", str(response_path), "--write-out", "%{http_code}"]
        if body is not None:
            payload_path = directory / "request"
            payload_path.write_bytes(body)
            command += ["--request", "POST", "--data-binary", "@" + str(payload_path)]
        else:
            command += ["--location", "--max-redirs", "3", "--proto-redir", "=https"]
        command.append(url)
        result = subprocess.run(command, input="".join(f"{key}: {value}\n" for key, value in headers.items()), capture_output=True, text=True)
        if result.returncode:
            raise JobError(f"网络请求未确认完成（curl 退出码 {result.returncode}）；未自动重试，计费状态可能未知")
        return int(result.stdout), response_path.read_bytes()


def scrub(value, key):
    if isinstance(value, dict):
        return {name: scrub(child, key) for name, child in value.items() if name.lower() not in SECRET_FIELDS and name not in {"b64_json", "input_references", "inlineData"}}
    if isinstance(value, list):
        return [scrub(child, key) for child in value]
    if isinstance(value, str):
        if key:
            value = value.replace(key, "[redacted]")
        value = re.sub(r"data:image/[^\s\"]+", "[image data omitted]", value)
        value = re.sub(r"https?://[^\s\"]+", "[URL omitted]", value)
        return value[:1500]
    return None if isinstance(value, float) and not math.isfinite(value) else value


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def execute(args, env=None):
    env = os.environ if env is None else env
    config = connection(args, env)
    job_path = Path(args.job).expanduser().resolve()
    job, prompt, parameters, refs = prepare(job_path, config)
    endpoint, content_type, body = request(config, prompt, parameters, refs)
    out = Path(args.out).expanduser().resolve()
    if args.dry_run:
        return {"status": "dry_run", "adapter": config["adapter"], "model": config["model"], "endpoint": endpoint, "reference_count": len(refs), "requested_images": parameters["n"], "output": str(out), "network_requests": 0}
    key = env.get(config["api_key_env"], "") if config["auth"] == "key" else ""
    if config["auth"] == "key" and not key:
        raise JobError(f"缺少密钥环境变量 {config['api_key_env']}；不要把密钥放在任务文件中")
    if re.search(r"[\r\n]", key):
        raise JobError("密钥不能包含换行")
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError as error:
        raise JobError("输出目录已存在；请使用新的任务目录，以免覆盖文件或重复扣费") from error
    reference_metadata = [{name: value for name, value in ref.items() if name != "blob"} for ref in refs]
    write_json(out / "job.json", job)
    (out / "prompt.md").write_text(prompt + "\n", encoding="utf-8")
    write_json(out / "request-metadata.json", {"adapter": config["adapter"], "endpoint": endpoint, "model": config["model"], "prompt": prompt, "parameters": parameters, "references": reference_metadata})
    record = {"status": "started", "started_at": datetime.now(timezone.utc).isoformat(), "adapter": config["adapter"], "requested_model": config["model"], "endpoint": endpoint, "style": job.get("style", {}), "format": job.get("format", {}), "mode": job.get("mode", "generate"), "reference_count": len(refs), "cost_usd": None, "visual_review": "not_performed", "image_context": "local-only", "images": [], "issues": [], "output": str(out)}
    write_json(out / "result.json", record)
    started = time.monotonic()
    try:
        headers = {"Content-Type": content_type, "Accept": "application/json"}
        if key:
            headers[config["auth_header"]] = config["auth_prefix"] + key
        status, raw = http(endpoint, headers, body, config["timeout"])
        record["http_status"] = status
        try:
            response = json.loads(raw)
        except ValueError as error:
            raise JobError(f"接口返回 HTTP {status}，响应不是有效 JSON；未自动重试") from error
        if not isinstance(response, dict):
            raise JobError("响应 JSON 顶层不是对象")
        metadata = scrub({name: response[name] for name in ("id", "created", "model", "provider", "usage", "error") if name in response}, key)
        write_json(out / "response-metadata.json", {"http_status": status, **metadata})
        usage = response.get("usage") or {}
        cost = usage.get("cost") if isinstance(usage, dict) else None
        if cost is not None:
            try:
                cost = float(cost)
                if not math.isfinite(cost) or cost < 0:
                    raise ValueError()
                record["cost_usd"] = cost
            except (TypeError, ValueError):
                record["issues"].append("接口费用字段不合法，保留为未知")
        for name in ("model", "provider"):
            if name in metadata:
                record["reported_" + name] = metadata[name]
        if not 200 <= status < 300 or response.get("error"):
            error = metadata.get("error", {})
            raise JobError(f"接口请求失败 HTTP {status}：{json.dumps(error, ensure_ascii=False)}；未自动重试")
        images = response.get("data")
        if not isinstance(images, list) or not images:
            raise JobError("响应未包含图片；可能已计费，不自动重新生成")
        for i, item in enumerate(images):
            if not isinstance(item, dict):
                raise JobError("响应图片条目格式不合法")
            if item.get("b64_json"):
                try:
                    blob = base64.b64decode(item["b64_json"], validate=True)
                except (ValueError, TypeError) as error:
                    raise JobError("返回的图片 base64 无法解码") from error
            elif item.get("url"):
                image_status, blob = http(item["url"], {}, None, config["timeout"])
                if image_status != 200:
                    raise JobError("图片下载失败；生成可能已计费，不重新生成")
            else:
                raise JobError("图片条目没有 b64_json 或下载地址")
            info = inspect_image(blob, alpha=parameters.get("background") == "transparent")
            extension = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}[info["format"]]
            filename = f"image-{i + 1:02d}.{extension}"
            (out / filename).write_bytes(blob)
            record["images"].append({"file": filename, **info})
            if item.get("revised_prompt"):
                record["images"][-1]["revised_prompt"] = scrub(item["revised_prompt"], key)
            if parameters.get("background") == "transparent" and not (info.get("contains_transparency") and info.get("contains_visible_pixels")):
                record["issues"].append(f"{filename} 未同时包含可见和透明像素")
            requested_format = parameters.get("output_format")
            if requested_format and requested_format.lower().replace("jpg", "jpeg") != info["format"].lower():
                record["issues"].append(f"{filename} 的实际格式与请求不一致，已保留原始文件")
        if len(record["images"]) != parameters["n"]:
            record["issues"].append("实际图片数量与请求不一致")
        record["status"] = "completed_with_issues" if record["issues"] else "completed"
    except (JobError, OSError, ValueError) as error:
        record.update(status="failed_or_unknown", error=scrub(str(error), key))
    finally:
        record["elapsed_seconds"] = round(time.monotonic() - started, 3)
        write_json(out / "result.json", record)
        text = f"# 图像任务记录\n\n- 状态：{record['status']}\n- 接口：{record['adapter']}\n- 请求模型：{record['requested_model']}\n- 风格：{json.dumps(record['style'], ensure_ascii=False)}\n- 图片用途：{json.dumps(record['format'], ensure_ascii=False)}\n- API返回费用 USD：{record['cost_usd'] if record['cost_usd'] is not None else '未知'}\n- 耗时：{record['elapsed_seconds']} 秒\n- 最终提示词：prompt.md\n- 输入图用途与哈希：request-metadata.json\n- 图片仅保存本地，未进入聊天上下文；视觉效果未检查。\n"
        for image in record["images"]:
            text += f"\n- 原始图片：[{image['file']}]({image['file']})，{image['width']}×{image['height']}，{image['format']}\n"
        if record.get("error"):
            text += "\n错误：" + record["error"] + "\n"
        if record["issues"]:
            text += "\n待处理项：" + "；".join(record["issues"]) + "\n"
        (out / "record.md").write_text(text, encoding="utf-8")
    return record


def parser():
    result = argparse.ArgumentParser(description="执行已编写的绘图任务；模型和 API 连接来自外部配置。")
    result.add_argument("--job", required=True, help="任务 JSON；参考图相对路径以此文件所在目录为基准")
    result.add_argument("--out", required=True, help="新的输出目录，已有目录不会覆盖")
    result.add_argument("--config", help="外部连接配置 JSON；也可设置 IMAGE_CONFIG_FILE")
    result.add_argument("--adapter", help="单次覆盖接口类型")
    result.add_argument("--base-url", help="单次覆盖 API 根地址")
    result.add_argument("--model", help="单次覆盖模型标识")
    result.add_argument("--dry-run", action="store_true", help="仅校验配置与任务，不联网、不创建输出目录")
    return result


def main(argv=None):
    try:
        record = execute(parser().parse_args(argv))
        print(json.dumps(record, ensure_ascii=False))
        return 0 if record["status"] in {"completed", "dry_run"} else 1
    except (JobError, OSError, ValueError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
