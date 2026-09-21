"""Safe, optional-dependency system information collection."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SystemInfo:
    os: str
    python_version: str
    cpu: str
    cpu_count: int | None
    torch_version: str
    cuda_available: bool
    cuda_version: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _torch_info() -> tuple[str, bool, str]:
    if importlib.util.find_spec("torch") is None:
        return "not installed", False, "unavailable"

    try:
        import torch
    except Exception:
        return "unavailable", False, "unavailable"

    torch_version = str(getattr(torch, "__version__", "unavailable"))
    try:
        cuda_available = bool(torch.cuda.is_available())
    except Exception:
        cuda_available = False

    torch_cuda_version = getattr(getattr(torch, "version", None), "cuda", None)
    if cuda_available:
        cuda_version = str(torch_cuda_version or "unavailable")
    else:
        cuda_version = "unavailable"
    return torch_version, cuda_available, cuda_version


def get_system_info() -> SystemInfo:
    """Collect system information even when torch or CUDA is unavailable."""

    torch_version, cuda_available, cuda_version = _torch_info()
    cpu = platform.processor() or platform.machine() or "unknown"
    return SystemInfo(
        os=f"{platform.system()} {platform.release()}",
        python_version=platform.python_version(),
        cpu=cpu,
        cpu_count=os.cpu_count(),
        torch_version=torch_version,
        cuda_available=cuda_available,
        cuda_version=cuda_version,
    )


def current_python_executable() -> str:
    """Return the active Python executable path."""

    return sys.executable
