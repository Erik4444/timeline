"""
Auto-discovery of parser plugins.

Any .py file in this directory that contains a class inheriting from BaseParser
and defining SOURCE_NAME is automatically registered. No manual registration needed.
"""
from __future__ import annotations

import importlib
import inspect
import logging
from pathlib import Path

from timeline.parsers.base import BaseParser

logger = logging.getLogger(__name__)

_registry: dict[str, type[BaseParser]] = {}


def _discover() -> None:
    parsers_dir = Path(__file__).parent
    for module_path in sorted(parsers_dir.glob("*.py")):
        if module_path.name.startswith("_") or module_path.name == "base.py":
            continue
        module_name = f"timeline.parsers.{module_path.stem}"
        try:
            module = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BaseParser)
                    and obj is not BaseParser
                    and hasattr(obj, "SOURCE_NAME")
                ):
                    _registry[obj.SOURCE_NAME] = obj
                    logger.debug("Registered parser: %s", obj.SOURCE_NAME)
        except Exception:
            logger.exception("Failed to load parser module: %s", module_name)


_discover()


def get_parser(source_name: str) -> BaseParser | None:
    cls = _registry.get(source_name)
    return cls() if cls else None


def all_parsers() -> list[BaseParser]:
    return [cls() for cls in _registry.values()]


def detect_parser(path: Path) -> BaseParser | None:
    for parser in all_parsers():
        try:
            if parser.can_handle(path):
                return parser
        except Exception:
            pass
    return None


def list_parser_info() -> list[dict]:
    return [
        {
            "source_name": cls.SOURCE_NAME,
            "display_name": cls.DISPLAY_NAME,
            "description": cls.DESCRIPTION,
            "supported_extensions": cls.SUPPORTED_EXTENSIONS,
        }
        for cls in _registry.values()
    ]
