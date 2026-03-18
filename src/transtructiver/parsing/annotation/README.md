# Annotation System

This directory provides semantic annotation for CST nodes, enabling consistent identifier classification across languages (Python, Java, C++).

> **Note:** Annotation modules require Python 3.14 or higher. For setup and troubleshooting, see the [main project README](../../../../README.md).


## Builtin Profiling and Language Profiles

The `builtin_checker.py` module enables annotation of nodes as builtins using language-specific JSON profiles found in the `profiles/` subdirectory:

- `profiles/python_builtins.json`: Python built-in functions and types
- `profiles/java_builtins.json`: Java standard library classes and packages
- `profiles/cpp_builtins.json`: C++ STL types and functions

Builtin profiling is optional and enabled by default. It is mainly used to ensure builtin names can be excluded from transformation (e.g., renaming), so that standard library identifiers are not affected by mutation rules.

These JSON files are loaded at runtime to provide dictionaries of builtins for each language. The checker annotates nodes with a `builtin` semantic label if their text matches any builtin identifier.

**To add or update builtins:**
1. Edit or add a JSON file in `profiles/` for your language.
2. The checker will automatically load and use the new profile.
3. The checker will compare each node's text to both the keys and all values in the JSON profile; if a match is found, the node is annotated as a builtin.

## Extending with New Language Support

1. **Create a new annotator module** (e.g., `my_lang_annotator.py`).
2. **Implement a function** to annotate nodes (see [python_annotator.py](./python_annotator.py) for reference).
3. **Register your annotator** in [\_\_init__.py](./__init__.py) by importing and adding it to `__all__`.
4. **Map your language’s node types** to unified semantic labels in `annotator.py` for cross-language consistency.

### Example Skeleton

```python
def _annotate_node(node: Node) -> None:
    # Annotate a single node for your language
    pass

def annotate_my_lang(root: Node) -> None:
    # Walk the tree and call _annotate_node on each node
    pass
```

### Guidelines
- Import the `walk` function from `.annotation_utils` to use post-order traversal for context-aware annotation.
- Assign `node.semantic_label` based on declaration context and usage.
- Refer to [python_annotator.py](./python_annotator.py), [java_annotator.py](./java_annotator.py), and [cpp_annotator.py](./cpp_annotator.py) for patterns.
- Use the `is_builtin` function from [builtin_checker.py](./builtin_checker.py) to mark builtins using the JSON profiles.

## Usage

Annotations are used by mutation and verification modules to enable language-agnostic transformations and reporting.

---
