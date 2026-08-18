"""Formatting helpers for assistant responses."""

from datetime import datetime


class Formatter:
    """Format assistant output values for terminal display."""

    @staticmethod
    def display_name(object_name: str | None) -> str:
        if not object_name:
            return "(unknown)"
        label, separator, suffix = object_name.rpartition("_")
        value = label if separator and suffix.isdigit() else object_name
        return value.replace("_", " ").title()

    @staticmethod
    def value(value: object | None) -> str:
        if value is None:
            return "(unknown)"
        if isinstance(value, tuple):
            return ", ".join(str(part) for part in value)
        if isinstance(value, list):
            return ", ".join(str(item) for item in value) if value else "(none)"
        if hasattr(value, "value"):
            return str(value.value)
        return str(value)

    @staticmethod
    def timestamp(value: datetime | None) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value is not None else "(unknown)"

    @staticmethod
    def sections(items: list[tuple[str, str | list[str] | None]]) -> str:
        lines: list[str] = []
        for heading, content in items:
            lines.append(heading)
            if isinstance(content, list):
                lines.extend(content or ["(none)"])
            else:
                lines.append(content if content else "(none)")
            lines.append("")
        return "\n".join(lines).rstrip()
