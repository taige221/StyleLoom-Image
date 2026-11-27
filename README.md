# StyleLoom Image

English | [简体中文](README.zh-CN.md)

A reusable image creation skill with **30 visual styles**, **6 image formats**, and an externally configured execution backend. It covers photography, anime, hand drawing, 3D, crafted materials, print aesthetics, and abstract art.

An agent reads [SKILL.md](SKILL.md), selects the relevant style and format, and prepares a complete prompt. The Python runner sends the prepared job to the configured image API and saves the original image, prompt, parameters, and available usage/cost metadata.

Browse the [30-style image gallery](examples/style-gallery.md): one representative image per preset, labeled with the model and prompt revision, with links to the current English style prompts.

## What it supports

- Text-to-image, reference-guided generation, and edits that preserve specified parts of the source.
- Independent style and format presets: scene illustrations, avatars, diary covers, four-panel comics, stickers, and wallpapers.
- Explicit reference roles: identity/subject, style, composition, and edit target.
- Configurable OpenRouter Images and OpenAI-compatible Images protocols, including compatible proxies and local servers.
- Local-only image delivery by default. No generated image or base64 payload is printed into the conversation.

There is **no built-in default model, API address, or protocol selection**. Other native API protocols need their own adapter. The runner executes JSON jobs; natural-language interpretation and preset selection belong to the agent. Style and format presets use English primary prompts with Chinese reference text. The agent composes execution prompts and reference roles in English by default, while preserving required on-image text verbatim in its original language. Operational references remain in Chinese; the runner does not translate inputs.

## Setup

Requirements: Python 3.9+, `curl`, and Pillow. The shell examples below use macOS/Linux conventions.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Load [SKILL.md](SKILL.md) through your agent's skill mechanism. The skill identifier is `styleloom-image`; [agents/openai.yaml](agents/openai.yaml) provides optional UI metadata. You can also run already prepared jobs directly with the CLI.

## Configure a backend

Copy the blank template to a local configuration file:

```bash
mkdir -p .local
cp examples/connection.example.json .local/connection.local.json
```

Edit that copy and fill in `adapter`, `base_url`, and `model`. Choose `openrouter_images` or `openai_images`; use the actual API root, including its version prefix, rather than a complete generation-method URL. The template is not loaded automatically and contains no model or service default.

Set the key in the environment variable named by `api_key_env` (the template uses `IMAGE_API_KEY`). Keep the key outside JSON files and source control.

Alternatively, configure `IMAGE_API_ADAPTER`, `IMAGE_API_BASE_URL`, and `IMAGE_MODEL` directly in the process environment. `IMAGE_CONFIG_FILE` can point to an external JSON file. The runner does not automatically load `.env` files.

Connection precedence: single-call CLI overrides → environment variables → the selected external JSON file. Request parameters are merged separately: file `request_defaults` → `IMAGE_API_PARAMS` JSON → job `parameters`.

## Try a job without generating an image

[examples/generate.json](examples/generate.json) contains a complete gouache cat-avatar prompt and uses OpenAI-compatible `size` parameters. For an OpenRouter model that supports resolution tiers, replace `size` with `resolution` and `aspect_ratio`, for example `"resolution": "1K", "aspect_ratio": "1:1"`. Check the selected model's actual capabilities first.

```bash
python scripts/generate.py --config .local/connection.local.json --job examples/generate.json --out output/avatar --dry-run
```

Dry run validates local configuration, input files, and request construction. It makes no network request, does not need a key, and creates no output directory. It does not prove that the remote model supports every requested parameter.

Remove `--dry-run` when you intend to generate an image and accept the configured provider's charge:

```bash
python scripts/generate.py --config .local/connection.local.json --job examples/generate.json --out output/avatar
```

Use `--model`, `--adapter`, or `--base-url` for a single-call override. Output directories must be new. Failed or uncertain requests are recorded and are not automatically retried or routed to a different provider.

## References and edits

[examples/edit.json](examples/edit.json) changes only the color of one ceramic cup. Supply an appropriate real source and update its `references[].path` before running it. Reference paths are relative to the original job file; the example points to `tmp/reference.png` relative to the repository root.

Each reference has an explicit `role`. The runner appends the roles to the final prompt and transmits image bytes directly to the image API in the same order. A local path is never treated as a URL the provider can read. Style and format metadata are archived without being sent as API parameters.

Use a new output directory for each revision. Image identity, exact text, narrative consistency, and edit fidelity require visual review; successful HTTP requests and valid image files do not establish those properties.

## Outputs

Each actual run saves `job.json`, the actual `prompt.md`, request metadata with reference roles and hashes, response metadata when available, `result.json`, `record.md`, and the original PNG/JPEG/WebP image bytes. API keys and duplicate base64 image bodies are excluded from execution records.

The terminal returns paths and metadata only. Reported USD cost is retained when available; absent cost is recorded as unknown. Transparent-background requests are checked for real alpha transparency and visible pixels, without a visual assessment of the artwork. Preserve the original job location or rebind references from the resolved paths in request metadata when replaying an archived job.

See [execution details](references/execution.md) for configuration fields, protocol differences, and result statuses.

## Tests and current validation

```bash
python -m unittest discover -s tests -v
```

Tests cover execution, configuration, reference ordering, format metadata, preset/index consistency, portable documentation links, and the packaged examples. They use synthetic tiny fixtures and mocked image services; they do not spend credits or load the experimental artwork into the conversation.

The earlier Seedream 5.5 study generated all 30 style cases and 18 capability cases, plus supporting reference material. The user found the overall style separation suitable for a first version. A later targeted comparison used the configurable runner for five Seedream 5.5 images and three GPT Image 2.6 Sunburst images with Chinese candidate prompts. Ten revised version 2 English styles have since been visually tested in a new gardening scene with Seedream 5.5: five were considered style candidates, three partly matched, and two still missed their core requirements. A same-prompt Sunburst comparison of five of those styles improved 06, 20, and 25 to style candidates; 30 remained partial and 27 still missed multi-view reconstruction. These are single-image observations at different quality settings, with content issues recorded separately; the other 20 English styles remain visually untested. See the portable [validation summary](references/test-results.md) and [test prompt suite](references/test-prompts.md).

## Project layout

```text
SKILL.md                 Agent instructions and on-demand preset indexes
README.md                English quick start
README.zh-CN.md          Chinese quick start
requirements.txt         Python dependency declaration
LICENSE                  MIT license text
agents/                  Optional skill UI metadata
skill/                   30 complete visual style presets
formats/                 6 independent image-format presets
scripts/generate.py      Configurable image API runner
examples/                Style gallery, representative images, and job examples
references/              Execution details, test prompts, validation summary
tests/                   Offline execution and resource tests
output/                  Local run artifacts; ignored by Git
```

Add a style or format file and update its index in `SKILL.md`; run the tests to check consistency. To support a different API protocol, add its request/response adapter and corresponding tests.

## License

Released under the [MIT License](LICENSE). You may use, modify, and redistribute this project, including commercially, provided you retain the copyright and permission notices. The software is provided without warranty; see the license for the full terms.
