from utils.system_utils import current_python_executable, get_system_info


def test_system_info_does_not_require_gpu_or_torch() -> None:
    info = get_system_info()
    assert info.os
    assert info.python_version
    assert info.cpu
    assert isinstance(info.cuda_available, bool)
    assert info.torch_version in {"not installed", "unavailable"} or isinstance(
        info.torch_version, str
    )
    assert isinstance(info.as_dict(), dict)


def test_python_executable_is_available() -> None:
    assert current_python_executable()
