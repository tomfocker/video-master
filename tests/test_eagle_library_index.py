import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "video-master" / "scripts" / "eagle_library_index.py"
SPEC = importlib.util.spec_from_file_location("eagle_library_index", SCRIPT)
assert SPEC and SPEC.loader
INDEX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEX)


class EagleLibraryIndexTest(unittest.TestCase):
    def test_catalog_is_explicit_bgm_only_and_omits_source_paths(self):
        catalog = INDEX.build_catalog(
            [
                {
                    "id": "audio-1",
                    "name": "Calm bed",
                    "ext": "mp3",
                    "tags": ["calm", "bed"],
                    "folders": ["music"],
                    "filePath": "C:/private/library/calm-bed.mp3",
                    "thumbnailPath": "C:/private/library/thumb.png",
                },
                {"id": "image-1", "name": "Icon should never enter BGM catalog", "ext": "png"},
            ],
            mcp_url="http://127.0.0.1:41596/mcp",
        )
        self.assertEqual(catalog["summary"]["asset_count"], 1)
        self.assertEqual(catalog["assets"][0]["kind"], "audio")
        self.assertEqual(catalog["catalog_scope"], "curated-bgm")
        serialized = json.dumps(catalog, ensure_ascii=False)
        self.assertNotIn("private/library", serialized)
        self.assertNotIn("thumbnailPath", serialized)

    def test_refresh_preserves_curation_only_for_current_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "catalog.json"
            output.write_text(
                json.dumps(
                    {
                        "curation_by_id": {
                            "keep": {"mood": "calm"},
                            "removed": {"mood": "stale"},
                        }
                    }
                ),
                encoding="utf-8",
            )
            curation = INDEX.read_existing_curation(output, {"keep"})
            self.assertEqual(curation, {"keep": {"mood": "calm"}})

    def test_reads_existing_ids_without_retaining_the_full_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "catalog.json"
            output.write_text(json.dumps({"assets": [{"id": "BGM-1", "name": "Ignored"}, {"id": "BGM-2"}]}), encoding="utf-8")
            self.assertEqual(INDEX.read_existing_asset_ids(output), ["BGM-1", "BGM-2"])


if __name__ == "__main__":
    unittest.main()
