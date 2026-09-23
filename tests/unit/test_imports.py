import importlib

import pytest


MODULES = [
    "core",
    "core.detection.detector",
    "core.detection.schemas",
    "core.schemas.association",
    "core.schemas.tracking",
    "core.tracking.tracker",
    "core.tracking.interfaces",
    "core.tracking.bytetrack_adapter",
    "core.association.ppe_person_association",
    "core.association.interfaces",
    "core.rules.compliance_engine",
    "core.rules.temporal_filter",
    "core.events.event_engine",
    "core.events.event_state",
    "core.pipeline.inference_pipeline",
    "infra.database.database",
    "infra.database.repository",
    "infra.storage.snapshot_storage",
    "infra.storage.video_storage",
    "infra.tts.tts_service",
    "infra.llm.llm_client",
    "infra.llm.fallback",
    "scripts.prepare_dataset",
    "scripts.validate_dataset",
    "scripts.train",
    "scripts.evaluate",
    "scripts.infer_image",
    "scripts.infer_video",
    "scripts.infer_stream",
    "scripts.run_demo",
    "services.dataset_service",
    "services.dataset_conversion_service",
    "services.dataset_quality_service",
    "services.train_service",
    "services.val_service",
    "services.inference_service",
    "services.tracking_service",
    "services.compliance_service",
    "services.event_service",
    "services.report_service",
    "services.agent_service",
    "utils.config_loader",
    "utils.logging_utils",
    "utils.performance_utils",
    "utils.quality_metrics",
    "utils.system_utils",
    "web.Home",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_package_module_imports(module_name: str) -> None:
    assert importlib.import_module(module_name)
