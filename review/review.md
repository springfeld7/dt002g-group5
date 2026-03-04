# Repository Review — Group 5

**Course:** Applied Datateknik, Mid Sweden University  
**Group:** 5  
**Project name:** TranStructIVer: Semantics-Preserving Code Transformation  
**Repository:** https://github.com/springfeld7/dt002g-group5  
**Review date:** 2026-03-04  
**Reviewer:** Course examiner  

---

## 1. Repository Summary

### Project purpose
TranStructIVer is a modular Python framework for automated, semantics-preserving code transformation and verification. It targets datasets of source code snippets stored in Apache Parquet files, parses them into Concrete Syntax Trees (CSTs) using Tree-sitter, applies configurable transformation rules (e.g., identifier renaming, comment deletion, control-flow restructuring), verifies structural isomorphism between the original and mutated CSTs, and is intended to produce augmented datasets suitable for training machine-learning models on code.

### Technology stack
Python 3.14, tree-sitter and tree-sitter-language-pack (CST parsing), pandas + pyarrow (Parquet data loading), uv build system (`uv_build`), pytest (testing), black (code formatting), pre-commit hooks, GitHub Actions CI (pytest + black workflows).

### Current development state
Intermediate. A functional prototype exists (CLI, data loader, parser, rename-identifier rule, structural verifier). The production package (`src/transtructiver`) has clean abstractions (MutationRule ABC, MutationEngine, adapter pattern) and the full enum of planned transformation action types, but only one concrete transformation rule (`RenameIdentifiersRule`) is implemented in the main codebase. Most FR-4.x transformations, the external configuration file (FR-8), manifest generation (FR-5), dataset output (FR-9), and the summary log (FR-10) are not yet implemented. The README is empty.

---

## 2. Evidence-Based Checklist of Good Practices

Scale: **Yes / Partly / No / Unclear**

### 2.1 Structure and organization

**The repository has a clear and logical folder structure.**  
Assessment: Yes  
Evidence: `src/transtructiver/` (production code), `tests/` (matching subdirectories), `.github/workflows/`, `pyproject.toml`, `.pre-commit-config.yaml`. The prototype lives under `src/transtructiver/prototype/`.  
Comment: Layout follows Python packaging conventions cleanly. Placing the prototype inside the production `src/` tree is slightly unconventional but not harmful.

**Source code, tests, configuration, and documentation are separated appropriately.**  
Assessment: Yes  
Evidence: Source under `src/transtructiver/`, tests under `tests/` (with matching sub-packages `data_loading/`, `mutation/`, `parsing/`), CI config in `.github/workflows/`, project config in `pyproject.toml`.  
Comment: README is missing content, but the structural intent is correct.

**File and folder names are meaningful and consistent.**  
Assessment: Yes  
Evidence: `data_loader.py`, `parser.py`, `adapter.py`, `mutation_rule.py`, `mutation_types.py`, `verifier.py`, `cli.py` — all names clearly reflect their responsibility. Test files follow `test_<module>.py` convention.  
Comment: No inconsistencies found.

**The repository avoids unnecessary generated files or clutter.**  
Assessment: Yes  
Evidence: `uv.lock` is committed (appropriate for reproducibility). `.gitignore` present. No `__pycache__`, `.venv`, or build artefacts committed.  
Comment: Clean repository state.

### 2.2 Code quality

**The code appears correct and runnable.**  
Assessment: Partly  
Evidence: Prototype CLI (`proto-cli`), parser, data loader, rename-identifier rule, and verifier are all coherent and appear runnable. Entry points declared in `pyproject.toml`. However, `proto-cli` requires a `manifest.json` to be pre-generated; no generation code is found.  
Comment: The pipeline can be invoked but has a manual dependency on a pre-existing manifest file that is not automatically created.

**The code follows consistent style and coding conventions.**  
Assessment: Yes  
Evidence: Black formatter enforced via `.pre-commit-config.yaml` (`rev: 24.1.0`, `line-length = 100`) and a dedicated GitHub Actions workflow (`.github/workflows/black.yml`). All inspected files follow PEP 8 naming and formatting.  
Comment: Strong enforcement; no style violations visible.

**The code is readable and reasonably modular.**  
Assessment: Yes  
Evidence: `MutationRule` is an ABC; `MutationEngine` is decoupled from rules; `Parser` delegates Tree-sitter conversion to `adapter.py`; `DataLoader` is a single-responsibility class. Every public function and class has a full docstring with Args/Returns/Example sections.  
Comment: Modular design is one of the strengths of this repository.

**There are no major obvious code smells (duplication, overly large files, unclear naming).**  
Assessment: Yes  
Evidence: Largest inspected file is `adapter.py` at 247 lines; all others are under 130 lines. No obvious duplication. Some prototype code duplicates core logic (e.g., separate `mutation_rule.py` in both `prototype/mutation/` and `src/transtructiver/mutation/`) but this appears intentional while the production module matures.  
Comment: Minor redundancy between prototype and production modules; not a blocker.

### 2.3 Documentation

**The repository contains a clear README.**  
Assessment: No  
Evidence: `README.md` contains only a single dash character (`-`).  
Comment: This is the most significant documentation gap. There is no project overview, setup guide, or usage instructions for a new reader.

**The README explains how to install, run, and use the system.**  
Assessment: No  
Evidence: README is empty. `pyproject.toml` does declare entry-point scripts (`transtructiver`, `proto-cli`, `proto-mutate`, `proto-parse`, `proto-verify`), but there is no document explaining these to a user.  
Comment: A reader must reverse-engineer the CLI from `cli.py` and `pyproject.toml`.

**The documentation would help a new developer understand and contribute to the project.**  
Assessment: Partly  
Evidence: In-code docstrings are thorough (all classes and methods include Args, Returns, and Example). Architecture is inferrable from the folder structure. No higher-level documentation (architecture overview, onboarding guide, contributing guidelines) exists.  
Comment: Good inline documentation partially compensates for the missing README.

**Important design decisions or setup details are documented.**  
Assessment: Partly  
Evidence: `pyproject.toml` records build system, Python version requirement (>=3.14), and dependencies. The `prototype/` directory structure implies a deliberate separation of exploratory code from the stabilising production package, but this is nowhere stated.  
Comment: Key design decisions (prototype-vs-production split, manifest schema, mutation contract) are only evident from the code itself.

### 2.4 Testing

**The repository contains tests.**  
Assessment: Yes  
Evidence: `tests/test_node.py` (101 lines), `tests/data_loading/test_data_loader.py`, `tests/parsing/test_parser.py`, `tests/parsing/test_adapter.py`, `tests/mutation/test_mutation_rule.py`, `tests/mutation/test_mutation_types.py`. Six test modules covering the main production abstractions.  
Comment: Good coverage of the infrastructure layer.

**Tests are relevant to the main functionality.**  
Assessment: Yes  
Evidence: Tests cover `Node` (core data structure), `DataLoader` (FR-1), `Parser`/`adapter` (FR-2, FR-3), `MutationRule` ABC, and `MutationAction` metadata validation. `test_mutation_types.py` uses `@pytest.mark.parametrize` for exhaustive contract-violation cases.  
Comment: Tests are well-targeted. No integration tests for the full pipeline exist yet.

**Tests can be executed with clear instructions.**  
Assessment: Partly  
Evidence: `pyproject.toml` lists `pytest>=9.0.2` as a dev dependency; GitHub Actions workflow installs and runs `pytest -v`. No instructions in the README for running tests locally.  
Comment: CI handles automated runs, but a developer cannot easily discover the local test command without reading the workflow file.

**Tests appear to pass, or there is evidence that they have been run successfully.**  
Assessment: Yes  
Evidence: GitHub Actions pytest workflow is present and triggered on push to `main` and on pull requests. All merged PRs (40 PRs evidenced in commit messages) imply passing tests at merge time.  
Comment: No evidence of test failures in the inspected history.

### 2.5 Collaboration and development practices

**Commit history suggests incremental development.**  
Assessment: Yes  
Evidence: 86 commits total. Development moves from `Add .gitignore` → prototype data loader/mutation/parser → project restructure → node class → data loader (production) → parsing module → mutation ABC → transformation types. Each feature is introduced in a separate named branch.  
Comment: Clear, traceable progression.

**Commit messages are meaningful.**  
Assessment: Yes  
Evidence: Messages such as "Refactor MutationRecord schema to remove Optional types and clarify attributes", "Enhance parser functionality with discard criteria and add tests", "Extend action types and add strict metadata validation" describe the change precisely. Conventional commit prefixes (`fix:`, `refactor:`, `chore/`) are used consistently.  
Comment: Above-average quality commit messages throughout.

**There is evidence of collaboration between both students.**  
Assessment: Yes  
Evidence: `git shortlog -sn --all` shows Thomas Springfeldt (thsp1900): 59 commits; Loviza Sahlén (losa2300): 27 commits. Both identities confirmed in `pyproject.toml` authors list. 40 pull requests merged, with branch names indicating ownership (e.g., `feature/parsing-module`, `feature/transformation-create-abstract-base-class`).  
Comment: Collaboration is real and sustained. Commit distribution is uneven (roughly 68/32 split) but both students show substantive contributions.  

---

## 3. What Is Being Done Well

1. **Well-engineered abstractions.** The `MutationRule` ABC, `MutationEngine`, and `MutationAction` enum with validated metadata schemas establish a clean extension point — adding a new transformation requires only a new subclass, no changes to core logic. This directly addresses NFR-4.
2. **Rigorous automated quality gates.** Black formatting is enforced both via pre-commit hook and a dedicated GitHub Actions workflow; pytest runs on every push and PR. This level of CI automation is uncommon at this stage in the course.
3. **Thorough inline documentation.** Every class and public method carries a full docstring with functional description, typed Args/Returns, and a usage example, making the code navigable without a README.
4. **Incremental, PR-driven development.** 86 commits across 40+ merged pull requests demonstrate disciplined feature-branch workflow, with descriptive commit messages that accurately describe each change.
5. **Real collaboration from both students.** Both Thomas Springfeldt and Loviza Sahlén have committed substantive code across different modules, confirmed by the `pyproject.toml` authors list and commit history.

---

## 4. What Needs Improvement

1. **README is completely absent.** The file contains only `-`. A new developer or evaluator cannot determine what the project does, how to install dependencies, which Python version is required, or how to run the pipeline or the tests. This must be addressed immediately.
2. **Most transformation rules are not implemented.** Only `RenameIdentifiersRule` (FR-4.1) exists as a concrete production rule. FR-4.2 through FR-4.7 (comment deletion, comment normalisation, indentation normalisation, control-structure substitution, control-flow flattening, dead-code insertion) have their action types defined but no implementation. This is the largest functional gap relative to the requirements.
3. **No external configuration file.** FR-8 requires a config file to toggle and parameterise transformations and auditor thresholds. Currently all control is via CLI flags. No TOML/YAML/JSON config file for the pipeline was found.
4. **Manifest generation is missing.** FR-5 requires generating a manifest of applied transformations. `proto-cli` loads a pre-existing `manifest.json` but the code that creates this file was not found. The pipeline cannot produce a manifest automatically.
5. **No dataset output or summary log.** FR-9 (output augmented dataset of original/mutated pairs) and FR-10 (summary log of success rates) are absent. The CLI currently prints to stdout; no file is written and no statistics are aggregated.

---

## 5. Evaluation Against Requirements

### 5.1 Functional Requirements

| Requirement | Description | Status | Evidence | Comment |
|---|---|---|---|---|
| FR-1 | Load source code snippets from Apache Parquet files. | Implemented | `src/transtructiver/data_loading/data_loader.py` uses `pandas.read_parquet` with `pyarrow` engine. | Works; raises `FileNotFoundError` and `ValueError` on failure. |
| FR-2 | Parse input code snippets into CSTs using Tree-sitter. | Implemented | `src/transtructiver/parsing/parser.py` wraps `TSParser` from `tree-sitter`; `adapter.py` converts the result to internal `Node` objects. | Full CST including whitespace nodes is produced. |
| FR-2.1 | Support parsing of Python code snippets. | Implemented | `tree-sitter-python>=0.25.0` is a direct dependency; `tree-sitter-language-pack` also has Python support. | Tested via `tests/parsing/test_parser.py`. |
| FR-2.2 | Support parsing of Java code snippets. | Partly implemented | `tree-sitter-language-pack` supports Java; no Java-specific code path, test, or sample data found in the repository. | Language selection is done at runtime; Java should work in principle but is untested. |
| FR-3 | Discard code snippets that produce invalid CSTs or contain errors. | Implemented | `parser.py` defines `is_trivial()` and `is_meaningful()` predicates and checks `node.is_error`/`node.has_error` on the Tree-sitter node. | Tests in `tests/parsing/test_parser.py` cover discard behaviour. |
| FR-4 | Apply semantics-preserving transformations to valid CSTs. | Partly implemented | `MutationEngine` and `MutationRule` ABC are in place; only `RenameIdentifiersRule` is implemented as a production rule. | Infrastructure solid; 6 of 7 specific rules missing. |
| FR-4.1 | Support variable renaming with respect to lexical scope. | Partly implemented | `RenameIdentifiersRule` renames all identifiers by prefixing `x_`; no lexical-scope tracking (all identifiers renamed indiscriminately). | Scope-aware renaming is not implemented; the current rule is a placeholder. |
| FR-4.2 | Support total deletion of comments. | Not implemented | `MutationAction.DELETE` and its metadata schema are defined in `mutation_types.py`; no concrete `MutationRule` subclass exists. | Schema and contract are ready; implementation missing. |
| FR-4.3 | Support normalization of comment format and length. | Not implemented | `MutationAction.REFORMAT` defined in enum; no concrete rule. | — |
| FR-4.4 | Support normalization of indentation and spacing. | Not implemented | `MutationAction.REFORMAT` covers this semantically; no implementation. | — |
| FR-4.5 | Support substitution of logically equivalent control structures. | Not implemented | `MutationAction.SUBSTITUTE` with `parts_map` schema defined; no concrete rule. | Schema with `target`/`iterable`/`body` keys suggests a for→while substitution was planned. |
| FR-4.6 | Support control-flow flattening of conditional structures. | Not implemented | `MutationAction.FLATTEN` with `ref_map` schema defined; no concrete rule. | — |
| FR-4.7 | Support insertion of non-functional code segments. | Not implemented | `MutationAction.INSERT` defined; no concrete rule. | — |
| FR-5 | Generate a manifest describing all applied transformations. | Not implemented | `proto-cli` loads a pre-existing `manifest.json`; no code found that generates this file automatically. | Manifest consumption is implemented; manifest production is missing. |
| FR-6 | Verify transformations using structural isomorphism checks. | Implemented (prototype) | `src/transtructiver/prototype/verification/verifier.py` implements `SIVerifier` with recursive coordinate-based structural comparison, renamed-path tracking, and ignored-path support. | Integrated into `proto-cli` pipeline. |
| FR-7 | Provide a CLI to orchestrate the data augmentation pipeline. | Implemented (prototype) | `proto-cli` entry point in `pyproject.toml`; `prototype/cli.py` uses `argparse` to accept `filepath` and `--rules` arguments and runs the full prototype pipeline. | Production `transtructiver` entry point exists but body not found. |
| FR-8 | Use an external configuration file to manage execution parameters. | Not implemented | No TOML/YAML/JSON configuration file found. Parameters are passed as CLI arguments only. | — |
| FR-8.1 | Use configuration file to toggle and parameterize specific transformations. | Not implemented | Not present. | — |
| FR-8.2 | Use configuration file to define auditor thresholds and strictness levels. | Not implemented | Not present. | — |
| FR-9 | Output the augmented dataset containing original and mutated code snippet pairs. | Not implemented | `proto-cli` prints transformed code to stdout; no output file of paired samples is written. | — |
| FR-10 | Generate a summary log detailing semantics-preservation success rates. | Not implemented | `SIVerifier` tracks errors internally but no per-run summary or log file is generated. | — |

### 5.2 Non-Functional Requirements

| Requirement | Description | Status | Evidence | Comment |
|---|---|---|---|---|
| NFR-1 | Process code snippets with max latency of 2 seconds per record and min throughput of 30 records/min. | Unclear | No performance tests, benchmarks, or profiling code found. | Cannot be assessed from the repository alone. |
| NFR-2 | CLI and configuration usable without prior training through clear options and documentation. | Partly implemented | `proto-cli` uses `argparse` (options self-documented via `--help`); code docstrings are detailed. README is entirely absent — a user cannot know how to install or invoke the tool without reading the source. | Argparse mitigates risk; missing README is the gap. |
| NFR-3 | Not crash when encountering malformed or unsupported code snippets. | Partly implemented | `DataLoader.load()` catches `FileNotFoundError` and `ValueError`. `parser.py` has discard logic for error nodes and trivial snippets. No explicit tests for malformed input or unsupported language codes at the CLI level. | Defensive programming exists in data loading and parsing; edge-case resilience at the pipeline boundary is untested. |
| NFR-4 | Remain modular so new languages and transformations can be added without modifying core logic. | Implemented | `MutationRule` ABC allows new rules as subclasses; `RULE_REGISTRY` in `cli.py` maps names to classes without modifying the engine; `tree-sitter-language-pack` supports dozens of languages; `adapter.py` isolates Tree-sitter specifics. | Design explicitly supports extensibility. |

---

## 6. Overall Assessment

### Summary judgment
The repository demonstrates strong software-engineering practices: clean modular architecture, strict style enforcement, meaningful commit history, CI/CD, and thorough docstrings. The prototype pipeline (FR-1, FR-2, FR-3, partial FR-4.1, FR-6, FR-7) is functional and internally coherent. However, the project is significantly behind on the functional requirements. Of the 21 specific FRs, only 6–7 can be assessed as fully or mostly implemented, and the most visible gap for an outside evaluator — an empty README — means the repository is currently not self-explanatory. The priority work is implementing the transformation rules (FR-4.2–4.7), the configuration file (FR-8), manifest generation (FR-5), dataset output (FR-9/FR-10), and writing the README.

### Confidence in this review
High for structural observations, documentation gaps, test coverage, and collaboration evidence — all directly inspectable. Moderate for FR-4.1 (scope-aware renaming) and NFR-1 (performance) — the former requires deeper semantic analysis, the latter cannot be assessed without running the system on a real dataset.

### Limitations of this review
The review is based on static inspection of the repository at the time of cloning. No tests were executed locally. No Parquet dataset was available to run the pipeline end-to-end. The `transtructiver` production entry point (`transtructiver:main`) could not be located, so the state of the top-level CLI is uncertain.

---

## 7. Suggested Improvements

1. **Write the README.** At minimum it should cover: project purpose, prerequisites (Python 3.14, uv), installation steps (`uv sync`), how to run the prototype CLI (`proto-cli <file.parquet> --rules rename-identifier`), and how to run the tests (`pytest -v`). The inline docstrings are good, but a README is the entry point for every evaluator and new contributor.

2. **Implement the remaining transformation rules (FR-4.2–4.7).** The `MutationRule` ABC, `MutationAction` enum, and metadata-validation contracts are all in place. The next step is to write concrete subclasses: `DeleteCommentsRule`, `ReformatCommentsRule`, `NormalizeIndentationRule`, `SubstituteControlStructureRule`, `FlattenControlFlowRule`, and `InsertDeadCodeRule`. Each can be developed and tested independently using the existing pattern.

3. **Implement automatic manifest generation (FR-5).** `proto-cli` already loads and consumes a `manifest.json`, but no code creates it. The `MutationRecord` schema and `MutationEngine.applyMutations()` return value are the right building blocks: collect the records returned by each rule and serialise them to JSON before the verification step.

4. **Add an external configuration file (FR-8).** Replace the hard-coded rule list and any future threshold values with a TOML or YAML config file. `pyproject.toml` already uses TOML, so a `config.toml` with `[transformations]` and `[auditor]` sections would be consistent with the existing tooling. `argparse` can accept a `--config` path argument for the CLI.

5. **Produce output artefacts and a summary log (FR-9, FR-10).** After the pipeline processes all rows, write the original/mutated pairs to a new Parquet file and append an aggregate log (total snippets, per-rule success/failure counts, overall semantics-preservation rate) to a CSV or JSON file. The `SIVerifier` already tracks `success_count` and `errors` per snippet; aggregating these across the DataFrame loop is the remaining step.  
