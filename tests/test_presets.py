import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def frontmatter(path):
    """Read the flat scalar metadata used by these resource files."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not match:
        raise AssertionError(f"Missing resource metadata: {path}")
    result = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator or key in result:
            raise AssertionError(f"Invalid or duplicate metadata field: {path}: {line}")
        result[key] = value.strip().strip('"').strip("'")
    return result


class PresetTests(unittest.TestCase):
    def test_style_identifiers_and_filenames_are_consistent(self):
        paths = sorted((ROOT / "skill").glob("*.md"))
        self.assertTrue(paths)
        ids, types = [], []
        for path in paths:
            data = frontmatter(path)
            with self.subTest(path=path.name):
                self.assertRegex(data["id"], r"^\d{2,}$")
                self.assertGreater(int(data["id"]), 0)
                self.assertRegex(data["type"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                self.assertEqual(path.stem, data["id"] + "-" + data["type"])
                self.assertTrue(data["name"])
                self.assertGreater(int(data["version"]), 0)
            ids.append(data["id"])
            types.append(data["type"])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(types), len(set(types)))

    def test_style_index_covers_each_resource_exactly_once(self):
        entry = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\| (\d+) \| `([^`]+)` \| \[[^\]]+\]\((skill/[^)]+)\)", entry, re.M)
        indexed = [ROOT / target for _, _, target in rows]
        self.assertCountEqual(indexed, list((ROOT / "skill").glob("*.md")))
        self.assertEqual(len(indexed), len(set(indexed)))
        for sid, stype, target in rows:
            data = frontmatter(ROOT / target)
            self.assertEqual((sid, stype), (data["id"], data["type"]))

    def test_format_index_and_metadata_are_consistent(self):
        entry = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\| `([^`]+)` \| \[[^\]]+\]\((formats/[^)]+)\)", entry, re.M)
        indexed = [ROOT / target for _, target in rows]
        resources = list((ROOT / "formats").glob("*.md"))
        self.assertTrue(resources)
        self.assertCountEqual(indexed, resources)
        self.assertEqual(len(indexed), len(set(indexed)))
        for fid, target in rows:
            data = frontmatter(ROOT / target)
            self.assertEqual(fid, data["id"])
            self.assertEqual(Path(target).stem, fid)
            self.assertTrue(data["name"])
            self.assertGreater(int(data["version"]), 0)

    def test_distributed_markdown_links_do_not_require_local_artifacts(self):
        paths = [ROOT / "README.md", ROOT / "README.zh-CN.md", ROOT / "SKILL.md"]
        for directory in ["references", "skill", "formats"]:
            paths.extend((ROOT / directory).glob("*.md"))
        local_only = {"output", "tmp", ".local", ".venv", ".git"}
        for path in paths:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                destination = (path.parent / target.split("#", 1)[0]).resolve()
                with self.subTest(path=path.relative_to(ROOT), target=target):
                    self.assertTrue(destination.is_relative_to(ROOT))
                    self.assertTrue(destination.exists())
                    self.assertFalse(local_only & set(destination.relative_to(ROOT).parts))

    def test_connection_example_cannot_select_a_provider_or_model(self):
        example = json.loads((ROOT / "examples/connection.example.json").read_text())
        for key in ["adapter", "base_url", "model"]:
            self.assertEqual(example[key], "")
        self.assertEqual(example["request_defaults"], {})
        self.assertNotIn("api_key", example)

    def test_job_examples_reference_existing_preset_versions(self):
        styles = {frontmatter(path)["id"]: frontmatter(path) for path in (ROOT / "skill").glob("*.md")}
        formats = {frontmatter(path)["id"]: frontmatter(path) for path in (ROOT / "formats").glob("*.md")}
        for name in ["generate.json", "edit.json"]:
            job = json.loads((ROOT / "examples" / name).read_text())
            with self.subTest(name=name):
                self.assertTrue(job["prompt"].strip())
                if "id" in job["style"]:
                    style = styles[job["style"]["id"]]
                    for key in ["type", "name", "version"]:
                        self.assertEqual(str(job["style"][key]), style[key])
                else:
                    self.assertIn(job["style"]["type"], {"custom", "preserve-source"})
                if "format" in job:
                    fmt = formats[job["format"]["id"]]
                    self.assertEqual(job["format"]["name"], fmt["name"])
                    self.assertEqual(str(job["format"]["version"]), fmt["version"])
                self.assertNotIn("model", job.get("parameters", {}))
                self.assertNotIn("api_key", job)


if __name__ == "__main__":
    unittest.main()
