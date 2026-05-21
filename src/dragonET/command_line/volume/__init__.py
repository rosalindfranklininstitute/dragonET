from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from types import ModuleType

from dragonET.command_line.volume import rebin, select_sample_axis


NAME = "volume"


def get_modules() -> tuple[ModuleType, ...]:
    return (rebin, select_sample_axis)
