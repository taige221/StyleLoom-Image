import base64
import importlib.util
import io
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from PIL import Image

SPEC = importlib.util.spec_from_file_location("generate", Path(__file__).resolve().parents[1] / "scripts/generate.py")
generate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate)


def raster(fmt="PNG", transparent=False):
    stream = io.BytesIO()
    image = Image.new("RGBA" if transparent else "RGB", (2, 2), (255, 0, 0, 255) if transparent else (255, 0, 0))
    if transparent:
        image.putpixel((0, 0), (0, 0, 0, 0))
    image.save(stream, fmt)
    return stream.getvalue()


class GenerateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.job_path = self.root / "job.json"
        self.out = self.root / "result"
        self.job_path.write_text(json.dumps({"prompt": "只画一个无字红杯子", "style": {"id": "custom"}}))
        self.args = generate.parser().parse_args(["--job", str(self.job_path), "--out", str(self.out)])
        self.env = {"IMAGE_API_ADAPTER": "openrouter_images", "IMAGE_API_BASE_URL": "https://images.example.test/v1", "IMAGE_MODEL": "chosen-model", "IMAGE_API_KEY": "test-secret-never-persist"}

    def job(self, value):
        self.job_path.write_text(json.dumps(value, ensure_ascii=False))

    def response(self, blob=None, **kwargs):
        return 200, json.dumps({"data": [{"b64_json": base64.b64encode(blob or raster()).decode()}], **kwargs}).encode()

    def test_no_vendor_or_model_default(self):
        with self.assertRaisesRegex(generate.JobError, "缺少配置"):
            generate.execute(self.args, {})
        self.assertFalse(self.out.exists())

    def test_external_file_environment_and_cli_precedence(self):
        config = self.root / "connection.json"
        config.write_text(json.dumps({"adapter": "openai_images", "base_url": "https://file.example.test/v1", "model": "file-model", "request_defaults": {"size": "1024x1024", "n": 2}, "api_key_env": "MY_IMAGE_KEY"}))
        self.args.config = str(config)
        self.args.model = "one-request-model"
        env = {"IMAGE_MODEL": "environment-model", "IMAGE_API_PARAMS": '{"n": 1}'}
        cfg = generate.connection(self.args, env)
        self.assertEqual(cfg["adapter"], "openai_images")
        self.assertEqual(cfg["model"], "one-request-model")
        self.assertEqual(cfg["base_url"], "https://file.example.test/v1")
        self.assertEqual(cfg["api_key_env"], "MY_IMAGE_KEY")
        self.assertEqual(cfg["request_defaults"], {"size": "1024x1024", "n": 1})

    def test_dry_run_never_sends_or_creates_output(self):
        self.args.dry_run = True
        with patch.object(generate, "http", side_effect=AssertionError("network")):
            result = generate.execute(self.args, {k: v for k, v in self.env.items() if k != "IMAGE_API_KEY"})
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(result["endpoint"], "https://images.example.test/v1/images")
        self.assertFalse(self.out.exists())

    def test_openrouter_text_request_and_records(self):
        with patch.object(generate, "http", return_value=self.response(usage={"cost": 0.02}, model="reported-model")) as call:
            result = generate.execute(self.args, self.env)
        payload = json.loads(call.call_args.args[2])
        self.assertEqual(payload["model"], "chosen-model")
        self.assertEqual(payload["response_format"], "b64_json")
        self.assertNotIn("input_references", payload)
        self.assertEqual(result["cost_usd"], 0.02)
        self.assertEqual(result["reported_model"], "reported-model")
        self.assertEqual(result["visual_review"], "not_performed")
        self.assertEqual(result["status"], "completed")
        for name in ["job.json", "prompt.md", "request-metadata.json", "response-metadata.json", "result.json", "record.md", "image-01.png"]:
            self.assertTrue((self.out / name).is_file(), name)
        for path in self.out.glob("*.json"):
            self.assertNotIn(self.env["IMAGE_API_KEY"], path.read_text())
            self.assertNotIn('"b64_json"', path.read_text())

    def test_openrouter_reference_order_roles_and_real_mime(self):
        (self.root / "source.jpg").write_bytes(raster("JPEG"))
        (self.root / "source.png").write_bytes(raster())
        prompt = 'Preserve the identity and change the composition. Render this text verbatim: "今天也很喜欢你".'
        self.job({"prompt": prompt, "references": [{"path": "source.jpg", "role": "Identity only"}, {"path": "source.png", "role": "Composition only"}]})
        with patch.object(generate, "http", return_value=self.response()) as call:
            result = generate.execute(self.args, self.env)
        payload = json.loads(call.call_args.args[2])
        self.assertTrue(payload["input_references"][0]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertTrue(payload["input_references"][1]["image_url"]["url"].startswith("data:image/png;base64,"))
        self.assertTrue(payload["prompt"].startswith(prompt + "\n\n"))
        self.assertIn("Input image roles (in the supplied order):\nImage 1: Identity only\nImage 2: Composition only", payload["prompt"])
        self.assertEqual((self.out / "prompt.md").read_text().strip(), payload["prompt"])
        self.assertEqual(result["reference_count"], 2)

    def test_openai_generation_path_and_custom_model(self):
        self.env["IMAGE_API_ADAPTER"] = "openai_images"
        self.env["IMAGE_MODEL"] = "another-model"
        self.job({"prompt": "红杯子", "parameters": {"size": "1024x1024"}})
        with patch.object(generate, "http", return_value=self.response()) as call:
            generate.execute(self.args, self.env)
        self.assertTrue(call.call_args.args[0].endswith("/images/generations"))
        payload = json.loads(call.call_args.args[2])
        self.assertEqual(payload["model"], "another-model")
        self.assertEqual(payload["size"], "1024x1024")
        self.assertNotIn("response_format", payload)

    def test_packaged_jobs_execute_with_metadata_only(self):
        project = Path(__file__).resolve().parents[1]
        example_dir = self.root / "examples"
        example_dir.mkdir()
        (self.root / "tmp").mkdir()
        (self.root / "tmp/reference.png").write_bytes(raster())
        self.env["IMAGE_API_ADAPTER"] = "openai_images"
        for name in ["generate.json", "edit.json"]:
            source = project / "examples" / name
            job = json.loads(source.read_text())
            local_job = example_dir / name
            local_job.write_text(source.read_text())
            self.args.job = str(local_job)
            self.args.out = str(self.root / name.removesuffix(".json"))
            with self.subTest(name=name), patch.object(generate, "http", return_value=self.response()) as call:
                result = generate.execute(self.args, self.env)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["style"], job["style"])
                self.assertEqual(result["format"], job.get("format", {}))
                self.assertEqual(result["image_context"], "local-only")
                if name == "generate.json":
                    payload = json.loads(call.call_args.args[2])
                    self.assertNotIn("style", payload)
                    self.assertNotIn("format", payload)
                    self.assertEqual(result["format"]["id"], "avatar")
                else:
                    self.assertEqual(result["reference_count"], 1)
                    self.assertTrue(call.call_args.args[0].endswith("/images/edits"))

    def test_openai_reference_generation_uses_multipart_edits(self):
        self.env["IMAGE_API_ADAPTER"] = "openai_images"
        source = raster("JPEG")
        (self.root / "reference.jpg").write_bytes(source)
        self.job({"mode": "generate", "prompt": "按参考身份画新场景", "references": [{"path": "reference.jpg", "role": "仅主体参考"}], "parameters": {"quality": "medium"}})
        with patch.object(generate, "http", return_value=self.response()) as call:
            generate.execute(self.args, self.env)
        url, headers, body, _ = call.call_args.args
        self.assertTrue(url.endswith("/images/edits"))
        self.assertTrue(headers["Content-Type"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="image[]"', body)
        self.assertIn(b"Content-Type: image/jpeg", body)
        self.assertIn(source, body)
        self.assertIn(b'name="quality"\r\n\r\nmedium', body)

    def test_url_result_download_has_no_api_credentials_and_keeps_native_jpeg(self):
        response = (200, json.dumps({"data": [{"url": "https://files.example.test/image?signature=private"}]}).encode())
        with patch.object(generate, "http", side_effect=[response, (200, raster("JPEG"))]) as call:
            result = generate.execute(self.args, self.env)
        self.assertEqual(call.call_args_list[1].args[1], {})
        self.assertIsNone(call.call_args_list[1].args[2])
        self.assertEqual(result["images"][0]["file"], "image-01.jpg")
        self.assertIsNone(result["cost_usd"])
        self.assertNotIn("signature=private", (self.out / "response-metadata.json").read_text())

    def test_api_failure_is_redacted_recorded_and_not_retried(self):
        error = {"error": {"message": "bad " + self.env["IMAGE_API_KEY"] + " data:image/png;base64,AAAA", "code": "invalid"}, "usage": {"cost": 0.008}}
        with patch.object(generate, "http", return_value=(400, json.dumps(error).encode())) as call:
            result = generate.execute(self.args, self.env)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result["status"], "failed_or_unknown")
        self.assertEqual(result["cost_usd"], 0.008)
        for path in self.out.glob("*"):
            if path.is_file():
                self.assertNotIn(self.env["IMAGE_API_KEY"].encode(), path.read_bytes())
        self.assertNotIn("data:image", json.dumps(result))

    def test_transport_failure_keeps_billing_unknown(self):
        with patch.object(generate, "http", side_effect=generate.JobError("timeout")) as call:
            result = generate.execute(self.args, self.env)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result["status"], "failed_or_unknown")
        self.assertIsNone(result["cost_usd"])
        self.assertTrue((self.out / "result.json").is_file())

    def test_curl_uses_stdin_for_auth_and_cleans_request_files(self):
        paths = []

        def fake_run(command, **kwargs):
            self.assertNotIn("private-test-key", " ".join(command))
            self.assertIn("Authorization: Bearer private-test-key\n", kwargs["input"])
            request_path = Path(command[command.index("--data-binary") + 1][1:])
            response_path = Path(command[command.index("--output") + 1])
            self.assertEqual(request_path.read_bytes(), b'{"prompt":"test"}')
            response_path.write_bytes(b'{"data":[]}')
            paths.extend([request_path, response_path])
            self.assertNotIn("--location", command)
            return SimpleNamespace(returncode=0, stdout="200")

        with patch.object(generate.subprocess, "run", side_effect=fake_run):
            status, body = generate.http("https://images.example.test/v1/images", {"Authorization": "Bearer private-test-key"}, b'{"prompt":"test"}', 30)
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"data":[]}')
        self.assertTrue(all(not path.exists() for path in paths))

    def test_curl_config_cannot_enable_generation_retries(self):
        class Handler(BaseHTTPRequestHandler):
            requests_seen = 0

            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                Handler.requests_seen += 1
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{}')

            def log_message(self, *args):
                pass

        curl_home = self.root / "curl-config"
        curl_home.mkdir()
        (curl_home / ".curlrc").write_text("retry = 1\nretry-delay = 1\n")
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {"CURL_HOME": str(curl_home), "NO_PROXY": "*", "no_proxy": "*"}):
                status, body = generate.http(f"http://127.0.0.1:{server.server_port}/images", {}, b'{}', 5)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        self.assertEqual(status, 503)
        self.assertEqual(body, b'{}')
        self.assertEqual(Handler.requests_seen, 1)

    def test_bad_image_preserves_reported_cost_without_retry(self):
        with patch.object(generate, "http", return_value=self.response(b"not-an-image", usage={"cost": 0.02})) as call:
            result = generate.execute(self.args, self.env)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result["status"], "failed_or_unknown")
        self.assertEqual(result["cost_usd"], 0.02)

    def test_missing_key_stops_before_creating_output(self):
        del self.env["IMAGE_API_KEY"]
        with patch.object(generate, "http", side_effect=AssertionError("network")):
            with self.assertRaisesRegex(generate.JobError, "缺少密钥"):
                generate.execute(self.args, self.env)
        self.assertFalse(self.out.exists())

    def test_transparency_is_checked_without_visual_review(self):
        self.job({"prompt": "透明背景红杯子", "parameters": {"background": "transparent", "output_format": "png"}})
        with patch.object(generate, "http", return_value=self.response(raster(transparent=True))):
            result = generate.execute(self.args, self.env)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["images"][0]["contains_transparency"])
        self.assertTrue(result["images"][0]["contains_visible_pixels"])

    def test_opaque_output_for_transparency_is_preserved_but_flagged(self):
        self.job({"prompt": "透明背景", "parameters": {"background": "transparent"}})
        with patch.object(generate, "http", return_value=self.response()):
            result = generate.execute(self.args, self.env)
        self.assertEqual(result["status"], "completed_with_issues")
        self.assertTrue(result["images"])
        self.assertTrue(result["issues"])

    def test_existing_directory_blocks_charge(self):
        self.out.mkdir()
        with patch.object(generate, "http", side_effect=AssertionError("network")):
            with self.assertRaisesRegex(generate.JobError, "已存在"):
                generate.execute(self.args, self.env)

    def test_invalid_jobs_never_reach_api(self):
        invalid = [
            {"mode": "edit", "prompt": "修改"},
            {"prompt": "a", "format": []},
            {"prompt": "a", "parameters": {"model": "hidden-default"}},
            {"prompt": "a", "parameters": {"api_key": "not-allowed"}},
            {"prompt": "a", "parameters": {"n": True}},
            {"prompt": "a", "parameters": {"output_format": []}},
            {"prompt": "a", "parameters": {"background": {}}},
            {"prompt": "a", "parameters": {"stream": True}},
            {"prompt": "a", "parameters": {"background": "transparent", "output_format": "jpeg"}},
            {"prompt": "a", "references": [{"path": "missing.png", "role": "主体"}]},
        ]
        for job in invalid:
            with self.subTest(job=job), patch.object(generate, "http", side_effect=AssertionError("network")):
                self.job(job)
                with self.assertRaises(generate.JobError):
                    generate.execute(self.args, self.env)

    def test_no_auth_local_endpoint_and_configurable_auth_header(self):
        self.env.update(IMAGE_API_AUTH="none", IMAGE_API_BASE_URL="http://127.0.0.1:8080/v1")
        with patch.object(generate, "http", return_value=self.response()) as call:
            generate.execute(self.args, self.env)
        self.assertNotIn("Authorization", call.call_args.args[1])
        self.args.out = str(self.root / "second")
        self.env.update(IMAGE_API_AUTH="key", IMAGE_API_AUTH_HEADER="x-api-key", IMAGE_API_AUTH_PREFIX="")
        with patch.object(generate, "http", return_value=self.response()) as call:
            generate.execute(self.args, self.env)
        self.assertEqual(call.call_args.args[1]["x-api-key"], self.env["IMAGE_API_KEY"])


if __name__ == "__main__":
    unittest.main()
