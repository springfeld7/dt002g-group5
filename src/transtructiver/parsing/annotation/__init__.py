"""Semantic annotation modules for different programming languages."""

from .annotator import annotate
from .python_annotator import annotate_python
from .java_annotator import annotate_java
from .cpp_annotator import annotate_cpp

__all__ = [
    "annotate",
    "annotate_python",
    "annotate_java",
    "annotate_cpp",
]
