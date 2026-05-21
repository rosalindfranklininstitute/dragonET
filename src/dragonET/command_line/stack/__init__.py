from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from types import ModuleType

from dragonET.command_line.stack import edit, predict, rebin, rot90, transform


NAME = "stack"


def get_modules() -> tuple[ModuleType, ...]:
    return (edit, predict, rebin, rot90, transform)
