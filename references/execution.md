# 执行与外部配置

先由加载 Skill 的 AI 理解用户内容、按需读取风格预设、解决明确冲突，再编写最终提示词和任务文件。`scripts/generate.py` 只执行任务，不选择风格、不补写用户情节、不调用其他语言模型。

代码不包含默认模型、默认 API 服务地址或默认接口类型，也不自动读取某款聊天工具的私有凭据目录。连接必须来自环境变量、外部 JSON 或单次命令行参数。Seedream 5.5 是之前测试所选模型，不是执行器的默认值。

## 1. 选择接口协议

| adapter | 文生图 | 有参考图或修改目标 | 响应 |
|---|---|---|---|
| `openrouter_images` | API 根地址后加 `/images`，JSON | 同一路径，图像编码为 `input_references` 中的 data URL | `data[].b64_json`，也兼容 `data[].url` |
| `openai_images` | API 根地址后加 `/images/generations`，JSON | `/images/edits`，multipart 文件上传，按顺序使用 `image[]` | `data[].b64_json` 或 `data[].url` |

两种协议都支持可配置的模型标识、API 根地址、鉴权请求头与额外请求参数。可以接相应协议的代理或本地服务；不能假定所有供应商的私有协议均兼容。其他接口需在脚本中增加请求适配及响应解析，并增加对应测试，不执行用户配置中的任意代码或 shell 命令。

API 根地址包含供应商要求的版本前缀，但不包含表中具体方法路径。例如 OpenRouter 的根地址为 `https://openrouter.ai/api/v1`，OpenAI 官方为 `https://api.openai.com/v1`。这些是说明示例，不会自动使用。远程服务使用 HTTPS；本机服务可使用 `http://localhost:端口/v1`。不关闭 TLS 验证；私有证书可通过 curl 的标准证书配置提供。

参考协议来源：[OpenRouter 图像接口](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)、[OpenAI 图像生成](https://developers.openai.com/api/reference/resources/images/methods/generate)、[OpenAI 图像编辑](https://developers.openai.com/api/reference/resources/images/methods/edit)。兼容协议不等于每个模型支持同一组参数，调用前应按实际模型核对。

## 2. 环境变量或外部文件

必需连接项：

| 环境变量 | 外部 JSON 字段 | 含义 |
|---|---|---|
| `IMAGE_API_ADAPTER` | `adapter` | 上表中的接口类型 |
| `IMAGE_API_BASE_URL` | `base_url` | API 根地址 |
| `IMAGE_MODEL` | `model` | 用户选定的模型标识 |
| `IMAGE_API_KEY_ENV` | `api_key_env` | 密钥所在环境变量的名称，未指定时读取 `IMAGE_API_KEY` |
| `IMAGE_API_AUTH` | `auth` | `key` 或显式 `none`；默认 `key` |
| `IMAGE_API_AUTH_HEADER` | `auth_header` | 默认 `Authorization`，可改为供应商要求的名称 |
| `IMAGE_API_AUTH_PREFIX` | `auth_prefix` | 默认 `Bearer `；无前缀时设为空字符串 |
| `IMAGE_API_PARAMS` | `request_defaults` | JSON 对象，保存该连接的请求参数，如尺寸、输出格式或路由 |
| `IMAGE_API_TIMEOUT` | `timeout` | 请求超时秒数，默认 180 |

`IMAGE_API_KEY_ENV` 存变量名，密钥值只存在该环境变量中，不写进连接 JSON、任务文件或 Skill。需要鉴权的实际调用缺少密钥时停止；试运行无需密钥。无需鉴权的本地服务应明确配置 `auth: none`。

连接文件放在用户选择的位置，例如个人配置目录、项目外部路径或未提交的本地目录，通过 `--config /实际路径/connection.json` 或 `IMAGE_CONFIG_FILE` 指定。执行器不会创建或修改该文件，也不扫描其他工具的凭据。

示意外部连接文件，示例地址和模型需用户替换后才能实际调用：

```json
{
  "adapter": "openai_images",
  "base_url": "https://your-provider.example/v1",
  "model": "YOUR_MODEL_ID",
  "api_key_env": "MY_IMAGE_API_KEY",
  "request_defaults": {
    "size": "1024x1024",
    "output_format": "png"
  }
}
```

连接优先级：命令行 `--adapter` / `--base-url` / `--model` → 对应环境变量 → 外部文件。`--config` 优先于 `IMAGE_CONFIG_FILE` 选择文件。请求参数按“外部文件的 request_defaults → IMAGE_API_PARAMS → 任务 parameters”覆盖；覆盖为浅合并，嵌套对象整体替换。

用户本次指定模型时，用 `--model` 明确覆盖；用户指定另一供应商时，同时确认地址、协议和密钥来源，不能只换模型名而继续发往错误的服务。配置缺失或接口不支持时说明问题，不能自动回退到历史测试模型。

## 3. 编写任务 JSON

例：外层已经选择 14 号水粉预设，将用户内容与其规则合成完整提示词。以下采用 `openai_images` 参数展示任务结构，不是默认场景或默认连接：

```json
{
  "mode": "generate",
  "user_request": "用水粉绘本风画两个人坐在沙发上追剧，温馨一点。",
  "style": {
    "id": "14",
    "type": "matte-gouache-storybook",
    "name": "哑光水粉绘本",
    "version": 1
  },
  "format": {
    "id": "scene-illustration",
    "name": "场景插画",
    "version": 1
  },
  "prompt": "两个人坐在沙发上一起追剧，氛围温馨。单幅横向画面，中景同时呈现两人和沙发。采用哑光水粉绘本画法，以不透明色块、概括阴影、干刷和自然笔触边缘塑造形体，纸纹适度可见，主体与环境的笔触和光照统一。避免塑料高光和平滑数码渐变。不添加其他人物、宠物、标题、logo或水印。",
  "references": [],
  "parameters": {
    "n": 1,
    "size": "1536x1024",
    "output_format": "png"
  }
}
```

- `prompt` 必须是完整提示词，不传“读取 14 号文件”之类工具执行不了的指令。`style` 与可选的 `format` 只用于留档，不当作 API 参数。脚本不会再次加载预设，也不会根据这两个元数据字段自动补写提示词或尺寸。
- `mode` 为 `generate` 或 `edit`；编辑必须提供实际目标图。`custom`、`preserve-source` 可写入 style 的 type，仍按入口规则组织提示词。
- `parameters` 是当前接口/模型的请求字段。OpenRouter 常用 `resolution`、`aspect_ratio`；OpenAI 兼容接口常用 `size`。不要将不兼容字段一起发送，不从“1K”擅自推导所有模型都接受的像素尺寸。
- 例如同一横向任务改用支持这些字段的 OpenRouter 模型时，可将上述 parameters 替换为 `{"n": 1, "resolution": "1K", "aspect_ratio": "4:3", "output_format": "png"}`。模型及地址仍从外部连接配置选择；画幅和尺寸要求应覆盖与它们冲突的连接默认参数。
- 本版每次支持请求 1—10 张，默认一次 1 张；异步任务、流式响应、动画、矢量和遮罩字段尚未实现。模型自身数量限制可能更低。
- 透明底明确指定 `background: transparent` 和兼容的 PNG/WebP 输出；脚本检查真实透明像素与可见像素。只检查文件和通道，不判断主体边缘质量。
- `references` 中每项为 `{"path": "本地路径", "role": "本次用途与保留项"}`。相对路径以输入任务文件所在目录为基准；每张限 50MB，支持 PNG/JPEG/WebP。实际数量以模型能力为准。
- 参考图顺序固定。脚本将用途说明附加到最终提示词，再按相同顺序传入实际文件；`prompt.md` 保存真正发送的最终文本，`request-metadata.json` 保存实际来源和哈希。
- 有参考图的新图任务，在 OpenAI 兼容协议中也走文件上传的 `/images/edits` 路径；任务的生成/修改意图仍保留在 mode 和提示词中。
- 提供修改目标时，提示词明确“只改什么、哪些保持不变”，不能只靠 `mode: edit` 表达保留要求。

## 4. 试运行与执行

依赖 Python 3.9+、curl，以及 Pillow；用 `python3 -m pip install -r requirements.txt` 安装 Python 依赖。Pillow 只用于本地文件校验和元数据，不进行画面编辑或视觉评判。配置和任务不写密钥。先把任务放在工作区临时位置，例如 `tmp/image-job.json`；输出使用一个尚不存在的新目录。

可复制的连接模板为 [connection.example.json](../examples/connection.example.json)，adapter、base_url、model 故意留空，必须在用户的外部副本中填写。完整任务示例见 [generate.json](../examples/generate.json) 和 [edit.json](../examples/edit.json)；编辑示例必须先绑定实际输入图。快速说明提供 [English](../README.md) 与 [简体中文](../README.zh-CN.md) 两个版本。

从 Skill 目录运行，或把脚本路径替换为其实际绝对路径：

```bash
python3 scripts/generate.py --job tmp/image-job.json --out output/my-image --dry-run
python3 scripts/generate.py --job tmp/image-job.json --out output/my-image
```

可附加 `--config /外部连接文件.json`，或 `--model 本次模型标识`。试运行校验文件、配置与请求构造，不联网、不校验远端模型实际可用性、不创建输出目录，也不产生绘图费用。实际调用前确认用户确实要求生成图片，讨论或仅写提示词时不执行第二条命令。

实际执行只发送一次生成请求。返回的是下载地址时再下载图片，不把 API 鉴权头转发给图片下载地址。curl 使用系统 TLS 验证；密钥经标准输入传递给请求头，不出现在命令行参数中。失败、超时或空图片不自动重新生成；费用未知时记为未知，不能记成零。已有输出目录拒绝覆盖，重新执行应先核查此前状态。

## 5. 产物与交付

每个任务生成：

```text
job.json                     输入任务，保留相对路径原文
prompt.md                    实际发送的完整提示词，含参考图用途
request-metadata.json        实际连接、模型、参数、输入文件用途及哈希
response-metadata.json       去除图片数据和凭据的响应元数据，收到有效JSON时保存
result.json                  状态、实际文件、尺寸、已知费用、耗时和问题
record.md                    便于阅读的摘要
image-01.png / .jpg / .webp   依据实际文件格式保存原始字节，不转换
```

`job.json` 的参考图相对路径以原始任务位置解释；重放时优先按 `request-metadata.json` 中已经解析的实际路径与哈希重新绑定，不把复制后的相对路径当成新位置。

成功时返回 `completed`；图片已保存但格式、数量或透明通道不符合请求时返回 `completed_with_issues`，进程退出码为 1；失败或状态不明为 `failed_or_unknown`，也返回 1。已知费用由接口提供，未提供美元费用的供应商只保留 token 等 usage，不擅自估算消费。

默认终端只输出 JSON 元数据，不输出 base64、下载签名地址或图像内容；不调用图片查看工具。向用户交付本地文件链接、所选风格与提示词位置，以及实际费用和未检查项。画面效果由用户检查，或在用户允许读取图片后另做视觉检查。

本地验证：`python3 -m unittest discover -s tests -v`。测试使用内存中的合成小图和模拟接口，不付费调用外部模型，不将历史生成图载入上下文。与具体供应商的实际兼容性仍需要使用对应外部配置做小样验证。
