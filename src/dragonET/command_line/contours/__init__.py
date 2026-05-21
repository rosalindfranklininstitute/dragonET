from __future__ import annotations
import typing

from dragonET.command_line.contours import extend, pick, refine, triangulate

if typing.TYPE_CHECKING:
    from types import ModuleType


NAME = "contours"


def get_modules() -> tuple[ModuleType, ...]:
    return (extend, pick, refine, triangulate)
