from enum import Enum


class ToolTag(Enum):
    """Tags for categorizing MCP tools by their access level."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
