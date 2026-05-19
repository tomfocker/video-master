import importlib.util
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EAGLE_CLIENT = ROOT / "skills" / "video-master" / "scripts" / "eagle_client.py"


def load_eagle_client_module():
    spec = importlib.util.spec_from_file_location("eagle_client", EAGLE_CLIENT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(b"\x00\x00" * 8000)


class EagleClientTest(unittest.TestCase):
    def test_resolves_original_item_file_from_library_path(self):
        eagle = load_eagle_client_module()
        with tempfile.TemporaryDirectory() as tmp:
            library = Path(tmp) / "音乐音效库.library"
            item_dir = library / "images" / "EAGLE123.info"
            write_wav(item_dir / "WHSH_SYNTH WHOOSH.wav")
            (item_dir / "WHSH_SYNTH WHOOSH_thumbnail.png").write_bytes(b"thumb")
            (item_dir / "metadata.json").write_text(
                '{"id":"EAGLE123","name":"WHSH_SYNTH WHOOSH","ext":"wav"}',
                encoding="utf-8",
            )

            resolved = eagle.resolve_item_file("EAGLE123", library)

            self.assertEqual(resolved.path, item_dir / "WHSH_SYNTH WHOOSH.wav")
            self.assertEqual(resolved.item_id, "EAGLE123")
            self.assertEqual(resolved.name, "WHSH_SYNTH WHOOSH")
            self.assertEqual(resolved.ext, "wav")

    def test_deduplicates_and_normalizes_library_history(self):
        eagle = load_eagle_client_module()

        paths = eagle.normalize_library_paths(
            [
                "/Volumes/剪辑盘/音乐音效库.library/",
                "/Volumes/剪辑盘/音乐音效库.library",
                "",
                "/Volumes/剪辑盘/灵感提示库.library",
            ]
        )

        self.assertEqual(
            [str(path) for path in paths],
            [
                "/Volumes/剪辑盘/音乐音效库.library",
                "/Volumes/剪辑盘/灵感提示库.library",
            ],
        )


if __name__ == "__main__":
    unittest.main()
