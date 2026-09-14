from __future__ import annotations

import typing

from dragonET.command_line.main import (
    align,
    generate_angles,
    make_video,
    new,
    project,
    reconstruct,
    refine,
    run,
    track,
)

if typing.TYPE_CHECKING:
    from types import ModuleType


NAME = "main"


def get_modules() -> tuple[ModuleType, ...]:
    return (
        new,
        align,
        project,
        refine,
        reconstruct,
        track,
        make_video,
        generate_angles,
        run,
    )
