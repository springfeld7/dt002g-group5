"""
Builtin Checker for Language Profiles

This module provides functions to load language builtins from JSON files and annotate AST/CST nodes
with semantic labels if their text matches any builtin identifier or type. Builtins are loaded as dictionaries
from per-language JSON files, and nodes are checked directly against keys and values (including lists).

Functions:
    load_builtins_from_json(path): Load builtins dictionary from a JSON file.
    make_profile_from_files(name, base_dir): Load builtins dict for a language from base_dir.
    normalize_name(raw_name): Strip whitespace from a name.
    is_builtin(raw_name, builtins_dict): Check if a name is a builtin (key or value).
    mark_builtin(node, builtins_dict): Annotate node with 'builtin' label if its text matches.
"""

import json
import os
from transtructiver.node import Node


def load_builtins_from_json(path: str) -> dict:
    """
    Load builtins dictionary from a JSON file.

    Args:
        path (str): Path to the JSON file containing builtins.

    Returns:
        dict: Dictionary of builtins (keys and lists of values).
    """
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def make_profile_from_files(name: str, base_dir: str):
    """
    Load builtins dictionary for a language from base_dir.

    Args:
        name (str): Language name (e.g., 'python', 'java', 'cpp').
        base_dir (str): Directory containing builtin JSON files.

    Returns:
        tuple: (language name, builtins dictionary)
    """
    path = os.path.join(base_dir, f"{name}_builtins.json")
    builtins_dict = load_builtins_from_json(path)
    return builtins_dict


def normalize_name(raw_name: str) -> str:
    """
    Strip whitespace from a name.

    Args:
        raw_name (str): The raw identifier or type name.

    Returns:
        str: The stripped name, or empty string if input is None.
    """
    return raw_name.strip() if raw_name else ""


def is_builtin(raw_name: str, builtins_dict: dict[str, str]) -> bool:
    """
    Check if a name is a builtin by searching keys and values in the builtins dictionary.

    Args:
        raw_name (str): The identifier or type name to check.
        builtins_dict (dict): Dictionary of builtins loaded from JSON.

    Returns:
        bool: True if the name is found as a key or value (including lists), False otherwise.
    """
    name = normalize_name(raw_name)
    if not name:
        return False
    if name in builtins_dict.keys():
        return True
    for v in builtins_dict.values():
        if isinstance(v, list):
            if name in v:
                return True
        elif isinstance(v, dict):
            for vv in v.values():
                if name == vv or (isinstance(vv, list) and name in vv):
                    return True
        elif name == v:
            return True
    return False


def mark_builtin(node: Node, builtins_dict: dict[str, str]):
    """
    Annotate a node with the semantic label 'builtin' if its text matches any builtin.

    Args:
        node (Node): The AST/CST node to annotate.
        builtins_dict (dict): Dictionary of builtins loaded from JSON.
    """
    if node.text and is_builtin(node.text, builtins_dict):
        node.semantic_label = "builtin"
