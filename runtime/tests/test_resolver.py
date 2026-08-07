import unittest
from runtime.src.config import ReasoningDepth
from runtime.src.resolver import ContextResolver

class TestContextResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = ContextResolver()

    def test_resolve_python_security_l3(self):
        ctx = self.resolver.resolve("Review Python security and system architecture")
        self.assertIn("modules/domains/languages/python/standards.md", ctx.target_modules)
        self.assertIn("modules/domains/engineering/security/standards.md", ctx.target_modules)
        self.assertEqual(ctx.reasoning_depth, ReasoningDepth.L3_DEEP)

    def test_resolve_l1_fast(self):
        ctx = self.resolver.resolve("Fix typo in comment")
        self.assertEqual(ctx.reasoning_depth, ReasoningDepth.L1_FAST)

if __name__ == '__main__':
    unittest.main()
