from __future__ import annotations
import argparse
import typing

from dragonET.command_line import main, contours, stack, volume

if typing.TYPE_CHECKING:
    from types import ModuleType


def add_subparser(
    parser: argparse.ArgumentParser,
    *modules,
    subparser_dest: str,
    subparser_title: str = "subcommands",
) -> argparse._SubParsersAction[argparse.ArgumentParser]:
    """Add subparsers from the modules passed.

    Args:
        parser (argparse.ArgumentParser): Parser that the subparsers will be added to.
        subparser_dest (str): Name of the attribute under which subcommand name will be stored.
        subparser_title (str, optional): Title for the sub-parser group in help output. Defaults to "subcommands".

    Returns:
        argparse._SubParsersAction[argparse.ArgumentParser]: Newly added subparser object with parsers.
    """
    subparser = parser.add_subparsers(title=subparser_title, dest=subparser_dest)
    for module in modules:
        module.add_arguments(
            subparser.add_parser(
                module.NAME,
                description=module.get_description(),
            )
        )
    return subparser


def _get_parser() -> argparse.ArgumentParser:
    """Get DragonET parser with subparsers.

    Returns:
        argparse.ArgumentParser: Top level DragonET parser.
    """
    parser = argparse.ArgumentParser(prog="DragonET")
    subparser = add_subparser(parser, *main.get_modules(), subparser_dest="main")
    for module in (contours, stack, volume):
        module_parser = subparser.add_parser(module.NAME)
        add_subparser(module_parser, *module.get_modules(), subparser_dest=module.NAME)

    return parser


def _run_submodule(module: ModuleType, namespace: argparse.Namespace) -> None:
    """Run the appropriate commands from 'module'.

    Args:
        module (ModuleType): Top level module inside dragonET.command_line.
        namespace (argparse.Namespace): Argparse namespace get arguments from.

    Raises:
        ValueError: If no submodule is found.
    """
    submodules_dict = {submodule.NAME: submodule for submodule in module.get_modules()}
    submodule = submodules_dict.get(getattr(namespace, module.NAME))
    if submodule is None:
        raise ValueError("Failed to get parse command")
    submodule.run(namespace)


def parse_args() -> None:
    """
    Parse CLI arguments to DragonET.
    """
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
