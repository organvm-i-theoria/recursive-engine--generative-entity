"""
RE:GE Output Formatting - Utilities for formatted output.

Provides:
- YAML output formatting
- CSV output formatting
- Colored output (using ANSI codes or rich library)
- Table formatting
"""

import json
from typing import Any, Dict, List, Optional, Union
import os

# Check for NO_COLOR environment variable (standard convention)
NO_COLOR = os.environ.get("NO_COLOR", "").lower() in ("1", "true", "yes")


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = "\033[0m"

    # Regular colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bold colors
    BOLD_RED = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"
    BOLD_YELLOW = "\033[1;33m"
    BOLD_BLUE = "\033[1;34m"
    BOLD_MAGENTA = "\033[1;35m"
    BOLD_CYAN = "\033[1;36m"
    BOLD_WHITE = "\033[1;37m"

    # Dim colors
    DIM = "\033[2m"

    @classmethod
    def disable(cls) -> None:
        """Disable all colors (set to empty strings)."""
        for attr in dir(cls):
            if attr.isupper():
                setattr(cls, attr, "")


# Disable colors if NO_COLOR is set
if NO_COLOR:
    Colors.disable()


# Charge tier colors
TIER_COLORS = {
    "LATENT": Colors.DIM,
    "PROCESSING": Colors.CYAN,
    "ACTIVE": Colors.GREEN,
    "INTENSE": Colors.YELLOW,
    "CRITICAL": Colors.BOLD_RED,
}


def colorize(text: str, color: str) -> str:
    """Apply color to text."""
    if NO_COLOR:
        return text
    return f"{color}{text}{Colors.RESET}"


def colorize_tier(tier_name: str) -> str:
    """Apply appropriate color to tier name."""
    color = TIER_COLORS.get(tier_name.upper(), Colors.WHITE)
    return colorize(tier_name, color)


def colorize_charge(charge: int) -> str:
    """Colorize charge value based on its tier."""
    if charge <= 25:
        return colorize(str(charge), Colors.DIM)
    elif charge <= 50:
        return colorize(str(charge), Colors.CYAN)
    elif charge <= 70:
        return colorize(str(charge), Colors.GREEN)
    elif charge <= 85:
        return colorize(str(charge), Colors.YELLOW)
    else:
        return colorize(str(charge), Colors.BOLD_RED)


def colorize_status(status: str) -> str:
    """Colorize status string."""
    status_lower = status.lower()
    if status_lower in ("success", "active", "activated", "completed"):
        return colorize(status, Colors.GREEN)
    elif status_lower in ("failed", "error", "halted"):
        return colorize(status, Colors.RED)
    elif status_lower in ("warning", "partial", "pending"):
        return colorize(status, Colors.YELLOW)
    else:
        return colorize(status, Colors.CYAN)


def colorize_organ(organ_name: str) -> str:
    """Colorize organ name."""
    return colorize(organ_name, Colors.BOLD_CYAN)


def colorize_mode(mode_name: str) -> str:
    """Colorize mode name."""
    return colorize(mode_name, Colors.MAGENTA)


def format_yaml(data: Any, indent: int = 2) -> str:
    """
    Format data as YAML-like output.

    Note: This is a simple implementation that doesn't require PyYAML.
    For complex nested structures, consider using the yaml library.
    """
    lines = []
    _format_yaml_recursive(data, lines, indent_level=0, indent_size=indent)
    return "\n".join(lines)


def _format_yaml_recursive(
    data: Any,
    lines: List[str],
    indent_level: int,
    indent_size: int,
) -> None:
    """Recursively format data as YAML."""
    indent = " " * (indent_level * indent_size)

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{indent}{key}:")
                _format_yaml_recursive(value, lines, indent_level + 1, indent_size)
            else:
                formatted_value = _format_yaml_value(value)
                lines.append(f"{indent}{key}: {formatted_value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{indent}-")
                _format_yaml_recursive(item, lines, indent_level + 1, indent_size)
            else:
                formatted_value = _format_yaml_value(item)
                lines.append(f"{indent}- {formatted_value}")
    else:
        lines.append(f"{indent}{_format_yaml_value(data)}")


def _format_yaml_value(value: Any) -> str:
    """Format a single YAML value."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        # Quote strings that might be ambiguous
        if (
            value == ""
            or value.lower() in ("true", "false", "null", "yes", "no")
            or any(c in value for c in ":#[]{}|>&*!?-")
        ):
            return f'"{value}"'
        return value
    else:
        return str(value)


def format_csv(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    delimiter: str = ",",
) -> str:
    """
    Format list of dictionaries as CSV.

    Args:
        data: List of dictionaries to format
        columns: Optional column order (default: keys from first item)
        delimiter: Field delimiter (default: comma)

    Returns:
        CSV formatted string
    """
    if not data:
        return ""

    # Determine columns
    if columns is None:
        columns = list(data[0].keys())

    lines = []

    # Header
    lines.append(delimiter.join(columns))

    # Data rows
    for row in data:
        values = []
        for col in columns:
            value = row.get(col, "")
            # Escape values containing delimiter or quotes
            str_value = str(value) if value is not None else ""
            if delimiter in str_value or '"' in str_value or "\n" in str_value:
                str_value = '"' + str_value.replace('"', '""') + '"'
            values.append(str_value)
        lines.append(delimiter.join(values))

    return "\n".join(lines)


def format_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> str:
    """
    Format data as ASCII table.

    Args:
        data: List of dictionaries to format
        columns: Optional column order (default: keys from first item)
        headers: Optional mapping of column keys to display headers

    Returns:
        ASCII table string
    """
    if not data:
        return "No data"

    # Determine columns
    if columns is None:
        columns = list(data[0].keys())

    # Get headers
    if headers is None:
        headers = {col: col.upper() for col in columns}

    # Calculate column widths
    widths = {}
    for col in columns:
        header_len = len(headers.get(col, col))
        max_data_len = max(len(str(row.get(col, ""))) for row in data)
        widths[col] = max(header_len, max_data_len) + 2  # padding

    # Build table
    lines = []

    # Header row
    header_row = "|"
    for col in columns:
        header_row += f" {headers.get(col, col):^{widths[col]-2}} |"
    lines.append(header_row)

    # Separator
    sep_row = "+"
    for col in columns:
        sep_row += "-" * widths[col] + "+"
    lines.insert(0, sep_row)
    lines.append(sep_row)

    # Data rows
    for row in data:
        data_row = "|"
        for col in columns:
            value = str(row.get(col, ""))
            data_row += f" {value:<{widths[col]-2}} |"
        lines.append(data_row)

    # Bottom separator
    lines.append(sep_row)

    return "\n".join(lines)


class OutputFormatter:
    """
    Unified output formatter for CLI commands.

    Supports multiple output formats and can be configured per-command.
    """

    def __init__(
        self,
        format_type: str = "text",
        use_color: bool = True,
        indent: int = 2,
    ):
        """
        Initialize formatter.

        Args:
            format_type: Output format (text, json, yaml, csv, table)
            use_color: Whether to use colored output (ignored for non-text formats)
            indent: Indentation for structured formats
        """
        self.format_type = format_type.lower()
        self.use_color = use_color and not NO_COLOR
        self.indent = indent

    def format(
        self,
        data: Any,
        columns: Optional[List[str]] = None,
    ) -> str:
        """
        Format data according to configured format type.

        Args:
            data: Data to format
            columns: Optional column specification for tabular formats

        Returns:
            Formatted string
        """
        if self.format_type == "json":
            return json.dumps(data, indent=self.indent, default=str)
        elif self.format_type == "yaml":
            return format_yaml(data, indent=self.indent)
        elif self.format_type == "csv":
            if isinstance(data, list):
                return format_csv(data, columns=columns)
            else:
                return format_csv([data], columns=columns)
        elif self.format_type == "table":
            if isinstance(data, list):
                return format_table(data, columns=columns)
            else:
                return format_table([data], columns=columns)
        else:
            # Default text format
            return self._format_text(data)

    def _format_text(self, data: Any, level: int = 0) -> str:
        """Format data as readable text."""
        indent = "  " * level
        lines = []

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{indent}{key}:")
                    lines.append(self._format_text(value, level + 1))
                else:
                    formatted_value = self._format_value(value)
                    lines.append(f"{indent}{key}: {formatted_value}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent}-")
                    lines.append(self._format_text(item, level + 1))
                else:
                    formatted_value = self._format_value(item)
                    lines.append(f"{indent}- {formatted_value}")
        else:
            lines.append(f"{indent}{self._format_value(data)}")

        return "\n".join(lines)

    def _format_value(self, value: Any) -> str:
        """Format a single value with optional color."""
        if value is None:
            return colorize("null", Colors.DIM) if self.use_color else "null"
        elif isinstance(value, bool):
            text = "true" if value else "false"
            color = Colors.GREEN if value else Colors.RED
            return colorize(text, color) if self.use_color else text
        elif isinstance(value, int):
            # Check if it might be a charge value
            if 0 <= value <= 100:
                return colorize_charge(value) if self.use_color else str(value)
            return str(value)
        else:
            return str(value)

    def success(self, message: str) -> str:
        """Format success message."""
        if self.use_color:
            return colorize(message, Colors.GREEN)
        return message

    def error(self, message: str) -> str:
        """Format error message."""
        if self.use_color:
            return colorize(message, Colors.RED)
        return message

    def warning(self, message: str) -> str:
        """Format warning message."""
        if self.use_color:
            return colorize(message, Colors.YELLOW)
        return message

    def info(self, message: str) -> str:
        """Format info message."""
        if self.use_color:
            return colorize(message, Colors.CYAN)
        return message


# Create default formatter instance
default_formatter = OutputFormatter()
