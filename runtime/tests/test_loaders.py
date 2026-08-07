import unittest
from runtime.src.config import AegisConfig
from runtime.src.loaders import KernelLoader, KnowledgeLoader

class TestLoaders(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig.load_from_env()
        self.kernel_loader = KernelLoader(self.config)
        self.knowledge_loader = KnowledgeLoader(self.config)

    def test_load_core_files(self):
        core_files = self.kernel_loader.load_core_files()
        self.assertEqual(len(core_files), 6)
        self.assertIn("core/kernel/constitution.md", core_files)
        tokens = self.kernel_loader.calculate_core_tokens(core_files)
        self.assertLess(tokens, 4000)

    def test_load_knowledge_module(self):
        content = self.knowledge_loader.load_module("modules/domains/languages/python/standards.md")
        self.assertIsNotNone(content)
        self.assertIn("Python", content)

if __name__ == '__main__':
    unittest.main()
