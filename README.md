# Transtructiver

Transtructiver is a modular framework for code mutation, semantic annotation, and verification across multiple programming languages.

> **Note:** This project requires Python 3.14 or higher. You can check your version with:
> ```sh
> python --version
> ```
> If you have an older version, download Python 3.14 from [python.org](https://www.python.org/downloads/).

## Quickstart

1. Install Python 3.14 (see note above).
2. Clone the repository:
	```sh
	git clone https://github.com/your-org/dt002g-group5.git
	cd dt002g-group5
	```
3. Install dependencies:
	- **A. Using [uv](https://github.com/astral-sh/uv) (recommended):**
		```sh
		uv sync
		# If you want to skip dev dependencies:
		uv sync --no-dev
		```
		uv will automatically create and manage a virtual environment for you.
	- **B. Using pip:**
		1. Create and activate a Python virtual environment:
			```sh
			python -m venv .venv
			.venv\Scripts\activate  # Windows
			source .venv/bin/activate  # Linux/Mac
			```
		2. Install dependencies:
			```sh
			pip install .
			# If you want to include dev dependencies:
			pip install .[dev]
			```

## Usage

Run the CLI:

- **With uv:**
    ```sh
    # Run the CLI with options
    uv run cli [options]

    # See the CLI help
    uv run cli --help

    # Example with a config file
    uv run cli <path-to-dataset> --config transtructiver.config.yaml
    ```

- **With pip/venv:**
    ```sh
    # Run the CLI with options
    python -m src.transtructiver.cli [options]

    # See the CLI help
    python -m src.transtructiver.cli --help

    # Example with a config file
    python -m src.transtructiver.cli <path-to-dataset> --config transtructiver.config.yaml
    ```

**Config file:**  
`transtructiver.config.yaml` can be used to configure which mutation rules to apply and other behavior. Include it in your command with the `--config` option as shown above.


## Testing

Run all tests:

- **With uv:**
	```sh
	uv run -m pytest tests/
	```
- **With pip/venv:**
	```sh
	pytest tests/
	```

## Extending the Software

- **Mutation Rules:**
  See `src/transtructiver/mutation/rules/README.md` for instructions on adding new mutation rules.

- **Language Support:**
  See `src/transtructiver/parsing/annotation/README.md` for instructions on supporting additional languages.

## Troubleshooting

- If you see errors about Python version, ensure you are using Python 3.14 or higher.
- If you see import errors, check that you installed dependencies and activated your virtual environment.
- If tests fail to collect, check for interpreter compatibility and standardized import patterns.

## CI and Local Parity

Continuous Integration (CI) runs on Python 3.14. For reproducible results, use Python 3.14 locally.

---
