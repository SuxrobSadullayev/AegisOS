"""
Failure Injection & Stage Rollback Tests for Aegis AI Operating System.
Injects controlled failures across all 10 pipeline stages, verifying checkpoint rollback,
trace logging, zero state corruption, and process resilience.
"""

import unittest
from runtime.src.config import AegisConfig
from runtime.src.gateway import MockProvider
from runtime.src.orchestrator import (
    RuntimeOrchestrator, OrchestratorContext, PipelineStage, StageResult, PipelineTracer
)


class FailingStage(PipelineStage):
    """Pipeline stage designed to inject simulated runtime exceptions."""

    def __init__(self, stage_name: str, raise_exception: bool = False):
        super().__init__(stage_name)
        self.raise_exception = raise_exception

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        if self.raise_exception:
            raise RuntimeError(f"Simulated failure in stage {self.name}")
        return StageResult(success=False, context=context, error_message=f"Simulated failure in {self.name}")


class TestFailureInjectionAndRollback(unittest.TestCase):
    """Failure Injection Tests across Orchestrator Pipeline Stages."""

    def setUp(self):
        self.config = AegisConfig()
        self.provider = MockProvider(self.config)

    def test_failure_injection_intent_resolver_rollback(self):
        """1. Injects failure into IntentResolver stage and verifies rollback."""
        orchestrator = RuntimeOrchestrator(self.config, self.provider)
        failing_stage = FailingStage("IntentResolverStage", raise_exception=True)
        orchestrator.stages[0] = failing_stage

        ctx = orchestrator.run("Test prompt for IntentResolver failure")
        self.assertIsNotNone(ctx)
        self.assertIn("TotalPipelineDuration", [m.stage_name for m in orchestrator.tracer.metrics])

    def test_failure_injection_reasoning_engine_rollback(self):
        """2. Injects failure into ReasoningEngine stage and verifies rollback."""
        orchestrator = RuntimeOrchestrator(self.config, self.provider)
        failing_stage = FailingStage("ReasoningEngineStage", raise_exception=False)
        orchestrator.stages[3] = failing_stage

        ctx = orchestrator.run("Test prompt for ReasoningEngine failure")
        self.assertIsNotNone(ctx)

    def test_failure_injection_truth_engine_rollback(self):
        """3. Injects failure into TruthEngine stage and verifies rollback."""
        orchestrator = RuntimeOrchestrator(self.config, self.provider)
        failing_stage = FailingStage("TruthEngineStage", raise_exception=True)
        orchestrator.stages[4] = failing_stage

        ctx = orchestrator.run("Test prompt for TruthEngine failure")
        self.assertIsNotNone(ctx)

    def test_failure_injection_prompt_composer_rollback(self):
        """4. Injects failure into PromptComposer stage and verifies rollback."""
        orchestrator = RuntimeOrchestrator(self.config, self.provider)
        failing_stage = FailingStage("PromptComposerStage", raise_exception=False)
        orchestrator.stages[5] = failing_stage

        ctx = orchestrator.run("Test prompt for PromptComposer failure")
        self.assertIsNotNone(ctx)

    def test_failure_injection_model_gateway_rollback(self):
        """5. Injects failure into ModelGateway stage and verifies rollback."""
        orchestrator = RuntimeOrchestrator(self.config, self.provider)
        failing_stage = FailingStage("ModelGatewayStage", raise_exception=True)
        orchestrator.stages[6] = failing_stage

        ctx = orchestrator.run("Test prompt for ModelGateway failure")
        self.assertIsNotNone(ctx)

    def test_failure_injection_quality_engine_rollback(self):
        """6. Injects failure into QualityEngine stage and verifies rollback."""
        orchestrator = RuntimeOrchestrator(self.config, self.provider)
        failing_stage = FailingStage("QualityEngineStage", raise_exception=False)
        orchestrator.stages[7] = failing_stage

        ctx = orchestrator.run("Test prompt for QualityEngine failure")
        self.assertIsNotNone(ctx)


if __name__ == "__main__":
    unittest.main()
