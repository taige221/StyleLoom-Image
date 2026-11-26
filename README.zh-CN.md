# StyleLoom Image

[English](README.md) | 简体中文

一个可复用的图像创作 Skill，包含 **30 种完整视觉风格**、**6 种独立图片用途**，执行后端由外部配置选择。覆盖摄影、动漫、手绘、三维、手作材质、印刷效果和抽象艺术。

加载 Skill 的 AI 读取 [SKILL.md](SKILL.md)，按需选择风格与用途，组织完整提示词。Python 执行器将准备好的任务发送到配置的图像接口，保存原图、提示词、参数及接口返回的用量和费用。

## 支持能力

- 纯文字生成、参考图引导生成，以及按明确保留项修改原图。
- 风格和图片用途独立组合：场景插画、头像、日记封面、四格漫画、表情贴纸、壁纸。
- 明确区分人物或主体、画风、构图、修改目标等参考图用途。
- 配置 OpenRouter 图像接口或 OpenAI 兼容图像接口，也可连接对应协议的代理及本地服务。
- 默认仅本地保存图片，不把生成图或 base64 数据回传到聊天上下文。

**不内置默认模型、API 地址或接口类型。** 其他原生协议需要新增适配器。执行器只处理 JSON 任务，自然语言理解和预设选择由加载 Skill 的 AI 完成。现有预设与详细操作文档使用中文。

## 安装依赖

需要 Python 3.9+、`curl` 和 Pillow。以下命令使用 macOS/Linux shell 语法。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

通过所用 AI 工具的 Skill 机制加载 [SKILL.md](SKILL.md)，标识为 `styleloom-image`；[agents/openai.yaml](agents/openai.yaml) 提供可选的界面展示信息。也可以直接使用命令行执行已经编写好的任务。

## 配置后端

把空白连接模板复制到本地配置位置：

```bash
mkdir -p .local
cp examples/connection.example.json .local/connection.local.json
```

编辑副本，填写 `adapter`、`base_url` 和 `model`。接口类型选择 `openrouter_images` 或 `openai_images`；根地址包括实际 API 所需的版本前缀，不包含具体生图方法路径。示例不会自动加载，也没有预选模型或服务。

密钥放到 `api_key_env` 指定的环境变量中，模板使用 `IMAGE_API_KEY`。密钥不写进 JSON 或版本库。

也可直接通过进程环境变量 `IMAGE_API_ADAPTER`、`IMAGE_API_BASE_URL`、`IMAGE_MODEL` 配置连接，或用 `IMAGE_CONFIG_FILE` 指向外部 JSON。执行器不会自动加载 `.env` 文件。

连接优先级：单次命令行覆盖 → 环境变量 → 选定的外部 JSON。请求参数另外按“文件中的 request_defaults → IMAGE_API_PARAMS JSON → 任务 parameters”合并。

## 先试运行

[examples/generate.json](examples/generate.json) 提供完整的水粉猫咪头像提示词，采用 OpenAI 兼容接口的 `size` 参数。使用支持分辨率档位的 OpenRouter 模型时，将 `size` 替换为 `resolution` 与 `aspect_ratio`，例如 `"resolution": "1K", "aspect_ratio": "1:1"`。具体参数以所选模型的能力为准。

```bash
python scripts/generate.py --config .local/connection.local.json --job examples/generate.json --out output/avatar --dry-run
```

试运行校验本地配置、输入文件和请求构造，不联网、不要求密钥、不创建输出目录，也不产生绘图费用。它不能证明远端模型实际支持每个请求参数。

确实要生成图片并接受所配置服务的费用时，再去掉 `--dry-run`：

```bash
python scripts/generate.py --config .local/connection.local.json --job examples/generate.json --out output/avatar
```

单次可用 `--model`、`--adapter` 或 `--base-url` 覆盖连接项。输出目录必须是新的；请求失败或状态不明时保留记录，不自动重试或切换服务。

## 参考图与修改

[examples/edit.json](examples/edit.json) 演示只修改一个陶瓷杯的颜色。执行前提供符合条件的实际原图，并更新 `references[].path`。相对路径以原始任务文件所在位置为基准；示例指向项目根目录下的 `tmp/reference.png`。

每张参考图都有明确的 `role`。执行器将用途说明追加到最终提示词，按同样顺序直接向绘图 API 传输图像字节，不把本地路径当成供应商可以读取的 URL。风格与用途的元数据只留档，不直接发送为 API 参数。

每次修改使用新的输出目录。身份保留、文字准确性、连续叙事及局部编辑效果需要视觉检查；HTTP 成功和文件可解码不能证明这些要求已经满足。

## 产物

每次实际执行保存 `job.json`、真正发送的 `prompt.md`、含参考图用途与哈希的请求元数据、可用时的响应元数据、`result.json`、`record.md`，以及原始 PNG/JPEG/WebP 图片字节。执行记录不包含密钥或重复的 base64 图片副本。

终端仅返回本地路径和元数据。接口提供美元费用时记录实际值，没有提供时记为未知；透明底请求会检查真实透明像素和可见像素，不对画面内容作视觉评价。重放归档任务时，应保留原始任务的位置，或按请求元数据中已经解析的路径重新绑定参考图。

完整配置字段、协议差异与状态说明见 [执行说明](references/execution.md)。

## 测试与当前验证状态

```bash
python -m unittest discover -s tests -v
```

测试覆盖执行器、配置优先级、参考图顺序、用途元数据、预设与索引一致性、文档链接及打包示例。使用合成小图和模拟接口，不消耗绘图额度，也不把本地实验样图载入上下文。

之前的 Seedream 5.5 实验已生成 30 个风格用例、18 个能力用例及辅助参考素材，用户粗看后认为整体区分度适合第一版。实验使用了独立的临时执行脚本，不代表当前可配置执行器已经通过真实供应商调用验证。详见可随项目分发的 [验证摘要](references/test-results.md) 与 [测试提示词](references/test-prompts.md)。

## 目录

```text
SKILL.md                 AI 入口与按需加载索引
README.md                默认英文快速说明
README.zh-CN.md          中文快速说明
requirements.txt         Python 依赖清单
LICENSE                  MIT 许可证原文
agents/                  可选的 Skill 界面展示信息
skill/                   30 份完整画风预设
formats/                 6 份独立图片用途预设
scripts/generate.py      可配置图像 API 执行器
examples/                空白连接模板与完整任务示例
references/              执行说明、测试提示词、验证摘要
tests/                   离线执行和资源一致性测试
output/                  本地任务产物，Git 忽略
```

新增风格或用途文件时，同步更新 `SKILL.md` 索引并运行测试。新增 API 协议时，补充请求／响应适配及对应测试。

## 许可证

本项目采用 [MIT 许可证](LICENSE)。允许使用、修改和再分发，包括商业用途；分发时须保留版权声明与许可声明。软件不提供担保，完整条款以许可证原文为准。
