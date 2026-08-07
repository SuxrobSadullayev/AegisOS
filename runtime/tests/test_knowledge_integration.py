import unittest
import threading
from runtime.src.config import AegisConfig
from runtime.src.knowledge import (
    KnowledgeLoader,
    CircularDependencyError,
    ModuleNotFoundError
)


class TestKnowledgeIntegration(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig.load_from_env()
        self.loader = KnowledgeLoader(self.config)

    def test_concurrent_multithreaded_loads(self):
        rel_path = "modules/domains/engineering/security/standards.md"
        results = []
        errors = []

        def worker():
            try:
                mod = self.loader.get_module(rel_path)
                results.append(mod.metadata.checksum)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 20)
        self.assertEqual(len(set(results)), 1)  # All threads got identical checksum

    def test_topological_dependency_sort(self):
        modules = self.loader.get_module_with_dependencies("modules/domains/engineering/architecture/standards.md")
        self.assertGreater(len(modules), 0)
        self.assertEqual(modules[-1].metadata.file_path.endswith("architecture/standards.md"), True)


if __name__ == '__main__':
    unittest.main()
