"""Unit tests for si_verifier.py

Covers verification of aligned trees, synchronized trees, deletions, insertions,
identity checks, strategy dispatch, and edge cases.
"""

from pathlib import Path
import pytest
from src.transtructiver.verification.si_verifier import SIVerifier
from src.transtructiver.node import Node
from src.transtructiver.mutation.mutation_manifest import MutationManifest, ManifestEntry
from src.transtructiver.mutation.mutation_rule import MutationRecord
from src.transtructiver.mutation.mutation_types import MutationAction
