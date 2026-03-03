"""Adapter utilities for converting Tree-sitter nodes to internal Nodes.

This module provides a conversion function that maps Tree-sitter's node
representation into the project's internal Node structure.
"""

from tree_sitter import Node as TSNode, Point
from ..node import Node


def _line_start_bytes(source_bytes: bytes) -> list[int]:
    """Build a mapping of line numbers to byte offsets.

    Creates a list where each index represents a line number and the
    value is the byte offset where that line starts in the source.

    Args:
        source_bytes (bytes): The source code as bytes.

    Returns:
        list[int]: List of byte offsets, where index N is the starting
            byte offset of line N. Line 0 always starts at byte 0.
    """
    starts = [0]
    for idx, byte in enumerate(source_bytes):
        if byte == 10:  # \n
            starts.append(idx + 1)
    return starts


def _byte_to_point(byte_offset: int, line_starts: list[int]) -> tuple[int, int]:
    """Convert a byte offset to a Point (row, column).

    Args:
        byte_offset (int): The byte offset to convert.
        line_starts (list[int]): List of byte offsets for each line.

    Returns:
        tuple[int, int]: The (row, column) corresponding to the byte offset.
    """
    # Find which line this byte offset is on
    row = 0
    for i, start in enumerate(line_starts):
        if byte_offset < start:
            break
        row = i

    # Column is the offset from the start of the line
    col = byte_offset - line_starts[row]
    return (row, col)


def _point_to_byte(point: Point, line_starts: list[int], code_len: int) -> int:
    """Convert a Tree-sitter Point to a byte offset.

    Translates a (row, column) point into an absolute byte position
    within the source code.

    Args:
        point (Point): Tree-sitter Point with row and column attributes.
        line_starts (list[int]): List of byte offsets for each line.
        code_len (int): Total length of source code in bytes.

    Returns:
        int: The absolute byte offset corresponding to the point.
            Returns code_len if the point is beyond the end of file.
    """
    row = point.row
    col = point.column

    if row >= len(line_starts):
        return code_len
    return min(line_starts[row] + col, code_len)


def _flush_whitespace(
    current_ws: str, current_start_byte: int, current_byte: int, line_starts: list[int]
) -> Node | None:
    """Flush accumulated whitespace into a Node.

    Args:
        current_ws (str): The accumulated whitespace string.
        current_start_byte (int): Byte offset where whitespace starts.
        current_byte (int): Current byte offset.
        line_starts (list[int]): List of byte offsets for each line.

    Returns:
        Node | None: A whitespace Node if current_ws is non-empty, None otherwise.
    """
    if current_ws:
        ws_start = _byte_to_point(current_start_byte, line_starts)
        ws_end = _byte_to_point(current_byte, line_starts)
        return Node(
            start_point=ws_start,
            end_point=ws_end,
            type="whitespace",
            text=current_ws,
        )
    return None


def _create_gap_nodes(
    start_point: Point, end_point: Point, source_bytes: bytes, line_starts: list[int], code_len: int
) -> list[Node]:
    """Create whitespace nodes for the gap between two points.

    Args:
        start_point (Point): The start point of the gap.
        end_point (Point): The end point of the gap.
        source_bytes (bytes): The full source bytes.
        line_starts (list[int]): List of byte offsets for each line.
        code_len (int): Total length of source code in bytes.

    Returns:
        list[Node]: List of whitespace/newline nodes for the gap.
    """
    gap_start_byte = _point_to_byte(start_point, line_starts, code_len)
    gap_end_byte = _point_to_byte(end_point, line_starts, code_len)
    return _space_nodes(source_bytes, gap_start_byte, gap_end_byte, line_starts)


def _space_nodes(
    source_bytes: bytes, start_byte: int, end_byte: int, line_starts: list[int]
) -> list[Node]:
    """Create whitespace/newline nodes for a byte range.

    Splits the byte range into individual whitespace and newline nodes,
    where each newline character becomes a separate "newline" node and
    contiguous non-newline whitespace becomes "whitespace" nodes.

    Args:
        source_bytes (bytes): The full source bytes.
        start_byte (int): Start position in bytes.
        end_byte (int): End position in bytes.
        line_starts (list[int]): List of byte offsets for each line.

    Returns:
        list[Node]: List of whitespace/newline nodes for the range.
    """

    if end_byte <= start_byte:
        return []

    text = source_bytes[start_byte:end_byte].decode("utf8")
    if text == "":
        return []

    nodes = []
    current_ws = ""
    current_start_byte = start_byte
    current_byte = start_byte

    for char in text:
        if char == "\n":
            # Flush any accumulated whitespace first
            ws_node = _flush_whitespace(current_ws, current_start_byte, current_byte, line_starts)
            if ws_node:
                nodes.append(ws_node)
            # Add newline node
            nl_start = _byte_to_point(current_byte, line_starts)
            nl_end = _byte_to_point(current_byte + 1, line_starts)
            nodes.append(
                Node(
                    start_point=nl_start,
                    end_point=nl_end,
                    type="newline",
                    text="\n",
                )
            )
            current_byte += 1
            current_start_byte = current_byte
            current_ws = ""
        else:
            # Accumulate whitespace
            current_ws += char
            current_byte += 1

    # Flush any remaining whitespace
    ws_node = _flush_whitespace(current_ws, current_start_byte, current_byte, line_starts)
    if ws_node:
        nodes.append(ws_node)

    return nodes


def convert_node(
    ts_node: TSNode,
    source_bytes: bytes,
    ws_map: dict | None = None,
) -> Node:
    """Convert a Tree-sitter node to the project's Node structure.

    Recursively converts a Tree-sitter parse tree into the internal Node
    representation. Uses Point-based spans to identify gaps between sibling
    nodes and creates separate whitespace/newline nodes for those gaps.

    Args:
        ts_node (TSNode): The Tree-sitter node to convert.
        source_bytes (bytes): The source code as bytes.
        ws_map (dict, optional): Whitespace map (unused, kept for compatibility).

    Returns:
        Node: The converted node with type, text (for leaves), children,
            and is_named status.
    """
    # Precompute line starts for Point-to-byte conversion
    line_starts = _line_start_bytes(source_bytes)
    code_len = len(source_bytes)

    if ts_node.child_count == 0:
        text = source_bytes[ts_node.start_byte : ts_node.end_byte].decode("utf8")
        children = []
    else:
        text = None
        children = []
        # For root-level nodes (module), start from (0, 0) to capture leading whitespace
        # For other nodes, start from the node's own start_point
        if ts_node.type == "module":
            previous_end_point = Point(0, 0)
        else:
            previous_end_point = ts_node.start_point

        for child in ts_node.children:
            # Convert Point span to bytes and create whitespace nodes if gap exists
            ws_nodes = _create_gap_nodes(
                previous_end_point, child.start_point, source_bytes, line_starts, code_len
            )
            children.extend(ws_nodes)

            # Recursively convert child node
            children.append(convert_node(child, source_bytes, ws_map))
            previous_end_point = child.end_point

        # Create whitespace nodes for trailing gap
        ws_nodes = _create_gap_nodes(
            previous_end_point, ts_node.end_point, source_bytes, line_starts, code_len
        )
        children.extend(ws_nodes)

    return Node(
        start_point=(ts_node.start_point.row, ts_node.start_point.column),
        end_point=(ts_node.end_point.row, ts_node.end_point.column),
        type=ts_node.type,
        text=text,
        children=children,
    )
