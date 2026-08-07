import unittest
from runtime.src.config import AegisConfig, QualityStatus
from runtime.src.gateway import MockProvider
from runtime.src.orchestrator import (
    RuntimeOrchestrator,
    OrchestratorContext,
    PipelineEvent,
    PipelineStage,
    StageResult,
    PipelineTracer
)

class CustomTestStage(PipelineStage):
    def __init__(self, should_fail: bool = False):
        super().__init__("CustomTestStage")
        self.should_fail = should_fail

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        if self.should_fail:
            return StageResult(success=False, context=context, error_message="CustomTestStage failure")
        meta = dict(context.metadata)
        meta["custom_stage_executed"] = True
        return StageResult(success=True, context=context.copy_with(metadata=meta))


class TestRuntimeOrchestrator(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig(max_retries=2)
        self.orchestrator = RuntimeOrchestrator(self.config)

    def test_full_pipeline_execution_success(self):
        ctx = self.orchestrator.run("Review Python security and system architecture")
        self.assertIsNotNone(ctx.model_response)
        self.assertIsNotNone(ctx.quality_result)
        self.assertEqual(ctx.quality_result.status, QualityStatus.PASS)
        self.assertIn("TotalPipelineDuration", [m.stage_name for m in self.orchestrator.tracer.metrics])

    def test_event_bus_subscription(self):
        received_events = []
        self.orchestrator.event_bus.subscribe(lambda evt: received_events.append(evt.event_type))
        self.orchestrator.run("Test task event bus")
        self.assertIn("PIPELINE_START", received_events)
        self.assertIn("STAGE_START", received_events)
        self.assertIn("STAGE_SUCCESS", received_events)
        self.assertIn("PIPELINE_COMPLETE", received_events)

    def test_plugin_stage_registration(self):
        custom_stage = CustomTestStage(should_fail=False)
        self.orchestrator.register_stage(custom_stage, position=1)
        ctx = self.orchestrator.run("Test plugin stage")
        self.assertTrue(ctx.metadata.get("custom_stage_executed"))

    def test_stage_failure_and_rollback(self):
        failing_stage = CustomTestStage(should_fail=True)
        self.orchestrator.register_stage(failing_stage, position=1)
        
        rollback_events = []
        self.orchestrator.event_bus.subscribe(lambda evt: rollback_events.append(evt.event_type))
        
        ctx = self.orchestrator.run("Test rollback on failure")
        self.assertIn("STAGE_FAIL", rollback_events)
        self.assertIn("ROLLBACK", rollback_events)

if __name__ == '__main__':
    unittest.main()
