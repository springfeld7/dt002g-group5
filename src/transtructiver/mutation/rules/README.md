# Mutation Rules

This directory contains modular mutation rules for transforming Concrete Syntax Trees (CSTs). Each rule implements the `MutationRule` interface and can be auto-discovered by the CLI.


## Extending with New Mutation Rules

1. **Create a new file** in this directory (e.g., `my_new_rule.py`), ensure the class name ends with `Rule` for auto-discovery by the CLI.
2. **Subclass `MutationRule`** from `mutation_rule.py`.
3. **Implement the `apply(self, root: Node) -> List[MutationRecord]` method**.
4. **Set a unique `rule_name`** class attribute for CLI discovery.

6. `mutation_rule.py` also provides some optional helper methods for creating mutation records, which you can use to simplify your implementation.


**Each `MutationRecord` must include:**
- `node_id`: a tuple (row, col) uniquely identifying the target node (synthetic nodes use negative coordinates)
- `action`: a `MutationAction` describing the type of transformation
- `metadata`: a dictionary with action-specific data, validated against the action's schema

> **Note:** Mutation rules and tests require Python 3.14 or higher. For setup and troubleshooting, see the [main project README](../../../../README.md).

### Example Skeleton

```python
from .mutation_rule import MutationRule, MutationRecord
from ...node import Node

class MyNewRule(MutationRule):
    rule_name = "my-new-rule"  # Optional

    def apply(self, root: Node):
        # Your mutation logic here
        return []
```

### Registering the Rule
- The CLI auto-discovers rules with a `rule_name` attribute.
- No manual registration is needed if you follow the pattern.


## Usage

Mutation rules are applied via the CLI or `transtructiver.config.yaml`. Each rule transforms the CST and produces a manifest of changes for verification and reporting.

---
# For Novel Mutations


Most new rules will use the current verification strategies by specifying the appropriate action type. Only if your mutation action is novel and not semantically compatible with the existing strategies should you implement a new verification strategy.

For a step-by-step guide to adding a new mutation action and verification strategy, see below.


## Adding a New Mutation Action and Verification Strategy

If your new mutation rule introduces a fundamentally new type of transformation (a new `MutationAction`) that is not covered by existing verification strategies, follow these steps:

### 1. Define a New MutationAction
- Edit `mutation_types.py` to add your new action to the `MutationAction` enum or class.
- Document the expected metadata schema for your action.

### 2. Implement the Mutation Rule
- Create your rule as described in the main `README.md` in this directory.
- Use your new action type in the `MutationRecord` objects you generate.

### 3. Add a Verification Strategy
- In `src/transtructiver/verification/strategies/`, create a new file (e.g., `my_action_strategy.py`).
- Implement a strategy class/function that can verify the correctness of your new mutation action.
- Register your strategy so it is discoverable by the verification system (see how existing strategies are registered).

### 4. Update Configuration and Documentation
- Ensure your new action and strategy are referenced in any relevant config files or manifests.
- Add tests for both the mutation rule and the verification strategy.

### 5. Example
- See existing files in `mutation_types.py` and `verification/strategies/` for patterns to follow.

---