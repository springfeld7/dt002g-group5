"""strategies/registry.py

This registry serves as a centralized mapping of MutationActions to their corresponding
VerificationStrategy implementations. This registry allows the SI Verifier to dynamically
select the appropriate validation logic for each node transformation based on the action type.
"""

from ...mutation.mutation_types import MutationAction
from .content_strategy import ContentVerificationStrategy
from .delete_strategy import DeleteVerificationStrategy
from .insert_strategy import InsertVerificationStrategy
from .substitute_strategy import SubstituteVerificationStrategy
from .flatten_strategy import FlattenVerificationStrategy


content_v = ContentVerificationStrategy()
delete_v = DeleteVerificationStrategy()
insert_v = InsertVerificationStrategy()
substitute_v = SubstituteVerificationStrategy()
flatten_v = FlattenVerificationStrategy()

STRATEGY_MAP = {
    MutationAction.RENAME: content_v,
    MutationAction.REFORMAT: content_v,
    MutationAction.DELETE: delete_v,
    MutationAction.INSERT: insert_v,
    MutationAction.SUBSTITUTE: substitute_v,
    MutationAction.FLATTEN: flatten_v,
}
