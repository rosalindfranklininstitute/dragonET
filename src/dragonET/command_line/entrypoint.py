from __future__ import annotations
import argparse
import typing

from dragonET.command_line import main, contours, stack, volume

if typing.TYPE_CHECKING:
    from types import ModuleType


def add_subparser(
    parser: argparse.ArgumentParser,
    *modules,
    parents: list[argparse.ArgumentParser] | None = None,
    subparser_title: str = "subcommands",
    dest: str | None = None,
) -> argparse._SubParsersAction[argparse.ArgumentParser]:
    if parents is None:
        parents = []
    subparser = parser.add_subparsers(title=subparser_title, dest=dest)
    for module in modules:
        module.add_arguments(
            subparser.add_parser(
                module.NAME,
                description=module.get_description(),
            )
        )
    return subparser


def _get_parser():
    parser = argparse.ArgumentParser(prog="DragonET")
    subparser = add_subparser(parser, *main.get_modules(), dest="main")
    for module in (contours, stack, volume):
        module_parser = subparser.add_parser(module.NAME)
        add_subparser(module_parser, *module.get_modules(), dest=module.NAME)

    return parser


def _run_submodule(module: ModuleType, namespace: argparse.Namespace) -> None:
    submodules_dict = {submodule.NAME: submodule for submodule in module.get_modules()}
    submodule = submodules_dict.get(getattr(namespace, module.NAME))
    if submodule is None:
        raise ValueError("Failed to get parse command")
    submodule.run(namespace)


def parse_args() -> None:
    parser = _get_parser()
    namespace = parser.parse_args()
    match namespace.main:
        case contours.NAME:
            _run_submodule(contours, namespace=namespace)
        case stack.NAME:
            _run_submodule(stack, namespace=namespace)
        case volume.NAME:
            _run_submodule(volume, namespace=namespace)
        case _:
            _run_submodule(main, namespace=namespace)


if __name__ == "__main__":
    parse_args()
