import unittest
import os
import tempfile
import time
from runtime.src.config import AegisConfig
from runtime.src.knowledge import (
    KnowledgeLoader,
    LoadedModule,
    ModuleMetadata,
    ModuleNotFoundError,
    CircularDependencyError,
    ChecksumMismatchError
)


class TestKnowledgeLoader(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig.load_from_env()
        self.loader = KnowledgeLoader(self.config)

    def test_lazy_load_python_module(self):
        rel_path = "modules/domains/languages/python/standards.md"
        mod = self.loader.get_module(rel_path)
        self.assertIsInstance(mod, LoadedModule)
        self.assertEqual(mod.metadata.module_id, "modules.domains.languages.python")
        self.assertIn("Python Engineering Standards", mod.content)
        self.assertGreater(len(mod.metadata.checksum), 0)

    def test_caching_and_hot_reload(self):
        rel_path = "modules/standards/naming.md"
        mod1 = self.loader.get_module(rel_path)
        mod2 = self.loader.get_module(rel_path)
        self.assertIs(mod1, mod2)  # In-memory cache hit

        # Force reload
        mod3 = self.loader.get_module(rel_path, force_reload=True)
        self.assertEqual(mod1.metadata.checksum, mod3.metadata.checksum)

    def test_missing_module_raises_error(self):
        with self.assertRaises(ModuleNotFoundError):
            self.loader.get_module("modules/non_existent_file.md")

    def test_checksum_verification(self):
        rel_path = "modules/standards/formatting.md"
        mod = self.loader.get_module(rel_path)
        self.assertTrue(self.loader.verify_checksum(rel_path, mod.metadata.checksum))

        with self.assertRaises(ChecksumMismatchError):
            self.loader.verify_checksum(rel_path, "invalid_checksum_hash_12345")

    def test_parse_metadata_header(self):
        header_text = "<!-- Module ID: domain.test | Version: 2.1.0 | Token Budget: ~800 | Depends: mod1, mod2 -->\n# Test Title\n## Purpose\nTest purpose"
        meta = self.loader.parse_metadata(header_text, "test.md")
        self.assertEqual(meta.module_id, "domain.test")
        self.assertEqual(meta.version, "2.1.0")
        self.assertEqual(meta.token_budget, 800)
        self.assertEqual(meta.dependencies, ["mod1", "mod2"])

    def test_metrics_collection(self):
        self.loader.get_module("modules/standards/versioning.md")
        metrics = self.loader.get_metrics()
        self.assertGreater(metrics["total_cached_modules"], 0)
        self.assertIn("total_load_time_ms", metrics)


if __name__ == '__main__':
    unittest.main()
