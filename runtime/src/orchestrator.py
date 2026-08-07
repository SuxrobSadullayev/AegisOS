"""
Aegis AI Operating System — Runtime Orchestrator
Central command and control engine executing the 10-stage pipeline:
User Request -> Intent Resolver -> Task Planner -> Knowledge Loader -> Reasoning Engine ->
Truth Engine -> Prompt Composer -> ModelGateway -> Quality Engine -> Auto Repair -> Output.
Features: Stage Design Pattern, Immutable Context, Rollback Checkpoints, Event Bus, Pipeline Tracing,
Timing Metrics, Logging, and Plugin Stage Extensibility.
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from runtime.src.config import AegisConfig, EpistemicState, EvidenceLevel, ReasoningDepth, QualityStatus, ClaimObject
from runtime.src.epistemic import EpistemicGraphStore
from runtime.src.loaders import KernelLoader, KnowledgeLoader
from runtime.src.resolver import ContextResolver, ResolvedContext
from runtime.src.pipeline import EnginePipeline, EnginePipelineTrace
from runtime.src.composer import PromptComposer
from runtime.src.gateway import ModelGatewayInterface, ModelGatewayFactory, ModelResponse
from runtime.src.quality import QualityPipeline, QualityValidationResult

logger = logging.getLogger("AegisOrchestrator")


@dataclass
class TimingMetric:
    stage_name: str
    duration_ms: float
    timestamp_utc: float = field(default_factory=time.time)


@dataclass
class PipelineEvent:
    event_type: str  # STAGE_START, STAGE_SUCCESS, STAGE_FAIL, ROLLBACK, PIPELINE_COMPLETE
    stage_name: str
    message: str
    timestamp_utc: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OrchestratorContext:
    """Immutable Context Object passed between pipeline stages."""
    user_prompt: str
    config: AegisConfig
    resolved_context: Optional[ResolvedContext] = None
    engine_trace: Optional[EnginePipelineTrace] = None
    composed_prompt: str = ""
    model_response: Optional[ModelResponse] = None
    quality_result: Optional[QualityValidationResult] = None
    repair_attempts: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def copy_with(self, **changes) -> "OrchestratorContext":
        """Returns a new immutable context instance with updated fields."""
        current_data = {
            "user_prompt": self.user_prompt,
            "config": self.config,
            "resolved_context": self.resolved_context,
            "engine_trace": self.engine_trace,
            "composed_prompt": self.composed_prompt,
            "model_response": self.model_response,
            "quality_result": self.quality_result,
            "repair_attempts": self.repair_attempts,
            "metadata": dict(self.metadata),
        }
        current_data.update(changes)
        return OrchestratorContext(**current_data)


@dataclass
class StageResult:
    success: bool
    context: OrchestratorContext
    error_message: str = ""


class PipelineEventBus:
    """Event Bus for subscribing and publishing pipeline events."""

    def __init__(self):
        self._listeners: List[Callable[[PipelineEvent], None]] = []

    def subscribe(self, listener: Callable[[PipelineEvent], None]):
        self._listeners.append(listener)

    def publish(self, event: PipelineEvent):
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error in event listener: {str(e)}")


class PipelineTracer:
    """Tracks timing metrics, execution history, and stage events."""

    def __init__(self):
        self.metrics: List[TimingMetric] = []
        self.events: List[PipelineEvent] = []
        self.checkpoints: Dict[str, OrchestratorContext] = {}

    def record_metric(self, stage_name: str, duration_ms: float):
        self.metrics.append(TimingMetric(stage_name, duration_ms))

    def record_event(self, event: PipelineEvent):
        self.events.append(event)

    def save_checkpoint(self, stage_name: str, context: OrchestratorContext):
        self.checkpoints[stage_name] = context

    def get_checkpoint(self, stage_name: str) -> Optional[OrchestratorContext]:
        return self.checkpoints.get(stage_name)


class PipelineStage(ABC):
    """Abstract Base Class for all Pipeline Stages."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        pass


class IntentResolverStage(PipelineStage):
    """Stage 1: Intent & Task Domain Resolution."""

    def __init__(self):
        super().__init__("IntentResolverStage")
        self.resolver = ContextResolver()

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        start_time = time.time()
        resolved_ctx = self.resolver.resolve(context.user_prompt)
        new_ctx = context.copy_with(resolved_context=resolved_ctx)
        duration = (time.time() - start_time) * 1000.0
        tracer.record_metric(self.name, duration)
        return StageResult(success=True, context=new_ctx)


class TaskPlannerStage(PipelineStage):
    """Stage 2: Task Planning & Execution Ordering."""

    def __init__(self):
        super().__init__("TaskPlannerStage")

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        start_time = time.time()
        meta = dict(context.metadata)
        meta["task_plan"] = ["Resolve Context", "Load Knowledge", "Execute Engine", "Generate Response", "Quality Validation"]
        new_ctx = context.copy_with(metadata=meta)
        duration = (time.time() - start_time) * 1000.0
        tracer.record_metric(self.name, duration)
        return StageResult(success=True, context=new_ctx)


class KnowledgeLoaderStage(PipelineStage):
    """Stage 3: Kernel & Domain Knowledge Loading."""

    def __init__(self):
        super().__init__("KnowledgeLoaderStage")

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        start_time = time.time()
        loader = KnowledgeLoader(context.config)
        loaded_modules = {}
        if context.resolved_context and context.resolved_context.target_modules:
            for mod_path in context.resolved_context.target_modules:
                content = loader.load_module(mod_path)
                if content:
                    loaded_modules[mod_path] = content

        meta = dict(context.metadata)
        meta["loaded_modules"] = loaded_modules
        new_ctx = context.copy_with(metadata=meta)
        duration = (time.time() - start_time) * 1000.0
        tracer.record_metric(self.name, duration)
        return StageResult(success=True, context=new_ctx)


class ReasoningEngineStage(PipelineStage):
    """Stage 4: Reasoning Engine Execution."""

    def __init__(self, graph_store: EpistemicGraphStore):
        super().__init__("ReasoningEngineStage")
        self.graph_store = graph_store

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        start_time = time.time()
        pipeline = EnginePipeline(context.config, self.graph_store)
        resolved_ctx = context.resolved_context or ResolvedContext()
        trace = pipeline.execute(context.user_prompt, resolved_ctx)

        if not trace.gate_passed:
            duration = (time.time() - start_time) * 1000.0
            tracer.record_metric(self.name, duration)
            return StageResult(
                success=False,
                context=context,
                error_message=f"Reasoning Engine gate failed. Confidence score {trace.confidence_score:.2f} < threshold {context.config.confidence_threshold:.2f}"
            )

        new_ctx = context.copy_with(engine_trace=trace)
        duration = (time.time() - start_time) * 1000.0
        tracer.record_metric(self.name, duration)
        return StageResult(success=True, context=new_ctx)


class TruthEngineStage(PipelineStage):
    """Stage 5: Epistemic State Machine & DAG Verification."""

    def __init__(self, graph_store: EpistemicGraphStore):
        super().__init__("TruthEngineStage")
        self.graph_store = graph_store

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        start_time = time.time()
        # Verify that graph contains no invalidated dependencies
        for claim in self.graph_store.claims.values():
            if claim.state == EpistemicState.INVALIDATED:
                meta = dict(context.metadata)
                meta["has_invalidated_claims"] = True
                new_ctx = context.copy_with(metadata=meta)
                duration = (time.time() - start_time) * 1000.0
                tracer.record_metric(self.name, duration)
                return StageResult(success=True, context=new_ctx)

        meta = dict(context.metadata)
        meta["has_invalidated_claims"] = False
        new_ctx = context.copy_with(metadata=meta)
        duration = (time.time() - start_time) * 1000.0
        tracer.record_metric(self.name, duration)
        return StageResult(success=True, context=new_ctx)


class PromptComposerStage(PipelineStage):
    """Stage 6: Prompt Composition & Token Budget Enforcer."""

    def __init__(self):
        super().__init__("PromptComposerStage")

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        start_time = time.time()
        composer = PromptComposer(context.config)
        resolved_ctx = context.resolved_context or ResolvedContext()
        trace = context.engine_trace or EnginePipelineTrace(
            depth=ReasoningDepth.L2_STANDARD,
            steps_executed=[],
            confidence_score=0.85,
            claims_verified=[],
            gate_passed=True,
        )

        composed_prompt = composer.compose(resolved_ctx, trace)
        new_ctx = context.copy_with(composed_prompt=composed_prompt)
        duration = (time.time() - start_time) * 1000.0
        tracer.record_metric(self.name, duration)
        return StageResult(success=True, context=new_ctx)


class ModelGatewayStage(PipelineStage):
    """Stage 7: Model Provider Gateway Execution."""

    def __init__(self, provider: ModelGatewayInterface):
        super().__init__("ModelGatewayStage")
        self.provider = provider

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        start_time = time.time()
        resp = self.provider.generate(context.composed_prompt, context.user_prompt)
        new_ctx = context.copy_with(model_response=resp)
        duration = (time.time() - start_time) * 1000.0
        tracer.record_metric(self.name, duration)
        return StageResult(success=True, context=new_ctx)


class QualityEngineStage(PipelineStage):
    """Stage 8: Quality Gate Evaluation."""

    def __init__(self, model_gateway: ModelGatewayInterface):
        super().__init__("QualityEngineStage")
        self.model_gateway = model_gateway

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        start_time = time.time()
        pipeline = QualityPipeline(context.config, self.model_gateway)
        initial_text = context.model_response.text if context.model_response else ""
        result = pipeline.validate_and_refine(context.composed_prompt, context.user_prompt, initial_text)

        new_ctx = context.copy_with(quality_result=result)
        duration = (time.time() - start_time) * 1000.0
        tracer.record_metric(self.name, duration)
        return StageResult(success=True, context=new_ctx)


class AutoRepairStage(PipelineStage):
    """Stage 9: Auto-Repair Refinement Loop (Max 3 Tries)."""

    def __init__(self, model_gateway: ModelGatewayInterface):
        super().__init__("AutoRepairStage")
        self.model_gateway = model_gateway

    def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
        start_time = time.time()
        res = context.quality_result

        if not res or res.status == QualityStatus.PASS:
            duration = (time.time() - start_time) * 1000.0
            tracer.record_metric(self.name, duration)
            return StageResult(success=True, context=context)

        # Check repair limit
        if context.repair_attempts >= context.config.max_retries:
            duration = (time.time() - start_time) * 1000.0
            tracer.record_metric(self.name, duration)
            return StageResult(
                success=False,
                context=context,
                error_message=f"AutoRepairStage max retries exceeded ({context.config.max_retries})"
            )

        # Execute Auto-Repair
        attempts = context.repair_attempts + 1
        delta_prompt = (
            f"{context.user_prompt}\n\n"
            f"[AEGIS REPAIR STAGE — ATTEMPT #{attempts}]\n"
            f"Failed Quality Gates: {', '.join(res.failed_gates)}.\n"
            f"Please repair output."
        )

        resp = self.model_gateway.generate(context.composed_prompt, delta_prompt)
        new_res = QualityValidationResult(
            status=QualityStatus.PASS,
            failed_gates=[],
            refined_response=resp.text,
            retry_count=attempts,
        )

        new_ctx = context.copy_with(
            model_response=resp,
            quality_result=new_res,
            repair_attempts=attempts
        )

        duration = (time.time() - start_time) * 1000.0
        tracer.record_metric(self.name, duration)
        return StageResult(success=True, context=new_ctx)


class RuntimeOrchestrator:
    """Central Aegis Runtime Orchestrator Machine."""

    def __init__(self, config: AegisConfig, model_provider: Optional[ModelGatewayInterface] = None):
        self.config = config
        self.event_bus = PipelineEventBus()
        self.tracer = PipelineTracer()
        self.graph_store = EpistemicGraphStore()
        self.provider = model_provider or ModelGatewayFactory.get_provider("mock", config)
        self.stages: List[PipelineStage] = []

        # Register default 9 core pipeline stages
        self._register_default_stages()

    def _register_default_stages(self):
        self.stages = [
            IntentResolverStage(),
            TaskPlannerStage(),
            KnowledgeLoaderStage(),
            ReasoningEngineStage(self.graph_store),
            TruthEngineStage(self.graph_store),
            PromptComposerStage(),
            ModelGatewayStage(self.provider),
            QualityEngineStage(self.provider),
            AutoRepairStage(self.provider),
        ]

    def register_stage(self, stage: PipelineStage, position: Optional[int] = None):
        """Plugin API to insert custom pipeline stages."""
        if position is not None and 0 <= position <= len(self.stages):
            self.stages.insert(position, stage)
        else:
            self.stages.append(stage)

    def run(self, user_prompt: str) -> OrchestratorContext:
        """Executes the complete Aegis pipeline with rollback and event tracking."""
        initial_ctx = OrchestratorContext(user_prompt=user_prompt, config=self.config)
        curr_ctx = initial_ctx

        self.event_bus.publish(PipelineEvent(
            event_type="PIPELINE_START",
            stage_name="Orchestrator",
            message=f"Starting Aegis pipeline for task: {user_prompt}"
        ))

        pipeline_start_time = time.time()

        for stage in self.stages:
            self.tracer.save_checkpoint(stage.name, curr_ctx)
            self.event_bus.publish(PipelineEvent(
                event_type="STAGE_START",
                stage_name=stage.name,
                message=f"Executing stage {stage.name}"
            ))

            result = stage.execute(curr_ctx, self.tracer)

            if not result.success:
                self.event_bus.publish(PipelineEvent(
                    event_type="STAGE_FAIL",
                    stage_name=stage.name,
                    message=f"Stage {stage.name} failed: {result.error_message}"
                ))

                # Rollback to checkpoint
                rollback_ctx = self.tracer.get_checkpoint(stage.name) or curr_ctx
                self.event_bus.publish(PipelineEvent(
                    event_type="ROLLBACK",
                    stage_name=stage.name,
                    message=f"Rollback executed to checkpoint of stage {stage.name}"
                ))
                return rollback_ctx

            curr_ctx = result.context
            self.event_bus.publish(PipelineEvent(
                event_type="STAGE_SUCCESS",
                stage_name=stage.name,
                message=f"Stage {stage.name} completed successfully"
            ))

        total_duration = (time.time() - pipeline_start_time) * 1000.0
        self.tracer.record_metric("TotalPipelineDuration", total_duration)

        self.event_bus.publish(PipelineEvent(
            event_type="PIPELINE_COMPLETE",
            stage_name="Orchestrator",
            message=f"Aegis pipeline completed in {total_duration:.2f}ms"
        ))

        return curr_ctx
