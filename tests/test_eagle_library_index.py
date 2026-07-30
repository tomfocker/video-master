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
    def test_catalog_is_video_focused_and_omits_source_paths(self):
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
                {"id": "note-1", "name": "Not video media", "ext": "txt"},
            ],
            include_other=False,
            mcp_url="http://127.0.0.1:41596/mcp",
        )
        self.assertEqual(catalog["summary"]["asset_count"], 1)
        self.assertEqual(catalog["assets"][0]["kind"], "audio")
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


if __name__ == "__main__":
    unittest.main()
