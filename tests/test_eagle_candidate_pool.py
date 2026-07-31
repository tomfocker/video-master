import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "video-master" / "scripts"
SCRIPT = SCRIPTS / "eagle_candidate_pool.py"
PROFILE_SCRIPT = SCRIPTS / "eagle_icon_library_profile.py"


def load_module(name: str, path: Path):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


POOL = load_module("eagle_candidate_pool", SCRIPT)
PROFILE = load_module("eagle_icon_library_profile", PROFILE_SCRIPT)


class FakeEagleClient:
    base_url = "http://127.0.0.1:41596/mcp"

    def __init__(self, items):
        self.items = items
        self.queries = []

    def query_items(self, query, *, full_details):
        self.queries.append((query, full_details))
        return list(self.items)

    def items_by_id(self, ids):
        return [item for item in self.items if item["id"] in ids]


class EagleCandidatePoolTest(unittest.TestCase):
    def test_plans_per_shot_candidates_without_leaking_file_paths(self):
        client = FakeEagleClient(
            [
                {"id": "SAT", "name": "卫星_Satellite", "ext": "png", "folders": ["tech"], "filePath": "C:/private/sat.png"},
                {"id": "ROCKET", "name": "火箭_Rocket", "ext": "png", "folders": ["vehicle"], "filePath": "C:/private/rocket.png"},
                {"id": "DOCTOR", "name": "医生_Doctor", "ext": "png", "folders": ["health"], "filePath": "C:/private/doctor.png"},
                {"id": "JPG", "name": "卫星照片", "ext": "jpg", "folders": ["tech"]},
            ]
        )
        request = {
            "schema_version": 1,
            "pools": [
                {"id": "space", "terms": ["卫星", "火箭"], "folder_ids": ["tech", "vehicle"], "extensions": ["png"]},
                {"id": "medical", "terms": ["医生"], "folder_ids": ["health"], "extensions": ["png"]},
            ],
            "shots": [
                {"id": "S01", "pool_ids": ["space"], "terms": ["卫星"], "limit": 2},
                {"id": "S02", "pool_ids": ["medical"], "terms": ["医生"], "limit": 2},
            ],
        }
        plan = POOL.plan_candidate_pool(request, client)
        self.assertEqual(client.queries, [("卫星 OR 火箭", False), ("医生", False)])
        self.assertEqual([item["id"] for item in plan["shots"][0]["candidates"]], ["SAT", "ROCKET"])
        self.assertEqual([item["id"] for item in plan["shots"][1]["candidates"]], ["DOCTOR"])
        serialized = json.dumps(plan, ensure_ascii=False)
        self.assertNotIn("C:/private", serialized)
        self.assertNotIn("JPG", serialized)

    def test_confirm_batch_validates_and_writes_only_confirmed_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sat.png"
            source.write_bytes(b"icon")
            client = FakeEagleClient(
                [
                    {"id": "SAT", "name": "卫星_Satellite", "ext": "png", "folders": ["tech"], "filePath": str(source)},
                    {"id": "ROCKET", "name": "火箭_Rocket", "ext": "png", "folders": ["vehicle"], "filePath": str(source)},
                ]
            )
            request = {
                "schema_version": 1,
                "pools": [{"id": "space", "terms": ["卫星", "火箭"], "folder_ids": ["tech", "vehicle"]}],
                "shots": [{"id": "S01", "pool_ids": ["space"], "limit": 2}],
            }
            plan = POOL.plan_candidate_pool(request, client)
            manifest_path, merged = POOL.apply_confirmed_selection(
                plan,
                {"schema_version": 1, "selections": [{"shot_id": "S01", "item_id": "SAT", "usage": "hero icon"}]},
                client,
                project=Path(tmp) / "project",
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual([asset["id"] for asset in manifest["assets"]], ["SAT"])
            self.assertEqual(merged[0]["id"], "SAT")
            self.assertEqual(manifest["shot_asset_assignments"], [{"shot_id": "S01", "item_id": "SAT", "role": "visual_asset", "usage": "hero icon"}])

    def test_shot_ranking_uses_full_pool_before_the_pool_display_limit(self):
        client = FakeEagleClient(
            [
                {"id": "ROCKET", "name": "aaa 火箭", "ext": "png", "folders": ["tech"]},
                {"id": "SAT", "name": "zzz 卫星", "ext": "png", "folders": ["tech"]},
            ]
        )
        plan = POOL.plan_candidate_pool(
            {
                "schema_version": 1,
                "pools": [{"id": "space", "terms": ["火箭", "卫星"], "folder_ids": ["tech"], "limit": 1}],
                "shots": [{"id": "S01", "pool_ids": ["space"], "terms": ["卫星"], "limit": 1}],
            },
            client,
        )
        self.assertEqual([candidate["id"] for candidate in plan["pools"][0]["candidates"]], ["ROCKET"])
        self.assertEqual([candidate["id"] for candidate in plan["shots"][0]["candidates"]], ["SAT"])

    def test_profile_keeps_categories_and_counts_without_item_records(self):
        class ProfileClient:
            def call_tool(self, name, arguments):
                if name != "item_count":
                    raise AssertionError(name)
                return 7

        profile = PROFILE.build_profile(
            [{"id": "root", "name": "original", "children": [{"id": "tech", "name": "科学技术", "children": []}]}],
            ProfileClient(),
            root_name="original",
            extension="png",
        )
        self.assertEqual(profile["summary"]["item_count"], 7)
        self.assertEqual(profile["categories"], [{"id": "tech", "name": "科学技术", "item_count": 7}])
        self.assertNotIn("assets", profile)


if __name__ == "__main__":
    unittest.main()
