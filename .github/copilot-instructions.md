# 🤖 copilot-instructions.md: AI Code Generation Guidelines

**Context:** This is a Python 3.14.5 data science and data engineering project managed by the Datalab. Your primary role is to act as an expert Python `engineer` and `reviewer`. All generated code and documentation must be in English.

---

## 🔒 1. Strict Security & Configuration Rules (CRITICAL)
* **NO SECRETS:** You MUST NOT hard-code passwords, API keys, tokens, URIs, or AWS credentials. 
* **NO ENVIRONMENT VARIABLES:** Direct usage of `os.getenv()` or `os.environ` is strictly **FORBIDDEN**.
* **Configuration Module:** All configuration and credentials MUST be accessed via: 
  `from dl_streamlit_pubquiz.modules.parameters import parameters`
* **No Raw SQL:** Writing raw SQL text or queries is strictly **FORBIDDEN**. All database operations MUST be handled exclusively via the internal `pondl` library. Use f-strings exclusively for standard Python strings.
---

## 🏗️ 2. Architectural & Stylistic Constraints
* **Design Pattern:** All backend logic MUST be implemented within a Python `class`. One class per file.
* **Naming Conventions:** Class names in `CamelCase` MUST strictly match the file name in `snake_case` (e.g., class `ArticleMaster` resides in `article_master.py`).
* **Function Limits:** Functions MUST NOT exceed 20 lines of code.
* **Arguments:** Always use explicit keyword arguments in function calls for clarity.
* **Modules:** The existing modules folder is strictly for cross-project shared code. Do not add project specific code here.
* **Folder Organization:** Organize files strictly into sub-folders that map directly to logical pipeline steps or architectural elements (e.g. `data_reading`, `data_preperation`, `data_writing`, `modelling`, etc.). Assume the user or the IDE will handle the physical directory creation based on your provided paths.
* **Constants:** All constants MUST be placed in a centralized `constants.py` file within the relevant module folder. 
* **Formatting & Code Quality Standards:** Code MUST adhere to the following strict standards:
    * **PEP 8:** Strict adherence to PEP 8 guidelines is required.
    * **Formatting:** Apply deterministic formatting constraints (e.g., consistent indentation, trailing commas, and standardized string quotes).
    * **Imports:** All imports MUST be alphabetically sorted and strictly grouped into three categories: Standard Library, Third-Party, and First-Party (Local).
    * **Linting:** Code must be strictly checked to ensure there are no unused imports, no unused variables, and no undefined names.

---

## 💻 3. Execution & Terminal Workflow
* **Code Execution:** NEVER run raw `python`. Determine the correct source directory yourself. Format: `PYTHONPATH=src AWS_DEFAULT_PROFILE=datalab-general poetry run python ...`
* **Terminal Commands:** When suggesting terminal commands for execution, Git, or testing, use non-blocking commands (`-m`, pipe input, `--no-edit`). 
* **Interactive Mode Ban:** Force non-interactive mode by setting `PAGER=cat` and `GIT_PAGER=cat`. Group commands efficiently using `&&`.

---

## 📝 4. Type Hinting & Documentation
* **Modern Type Hints:** Use PEP 604 type hints strictly (e.g., `str | None`, `list[str]`). 
* **Return Types:** Functions without a return value MUST be explicitly annotated with `-> None`.
* **Docstrings:** Use `Google-style` docstrings for every new or modified class and function.

---

## 🛠️ 5. Approved Libraries & Error Handling
* **Data Manipulation:** You MUST use `polars` (imported as `pl`). **NEVER** use `pandas` unless strictly required by a legacy API. Use Lazy API (`pl.scan_parquet()`) and native expressions.
* **Logging:** Use `loguru` exclusively. **NEVER** use `print()` or `import logging`. If using Sentry, you MUST set `send_default_pii=False`.
* **Exceptions:** Catch specific exceptions only. Bare `except:` blocks are forbidden.
* **AWS & DB:** Use `awswrangler` for S3 and the internal `pondl` library for database operations.

---

## 📂 6. File Path & Database Handling
* **Dynamic Paths:** Use `pathlib` for robust, dynamic path resolution (e.g., `PROJECT_ROOT = Path(__file__).resolve().parents[2]`). Do not use brittle hardcoded relative strings like `"../../data/"`.
* **Data Directory:** All data files reside in the root `data/` folder.
* **SQL Files:** Place raw `.sql` files strictly in the `sql/` directory. Prefix these files with `select_`, `table_`, or `view_`.

---

## ⚙️ 7. Data Orchestration & Inheritance (Facade + Base)
* **Pattern Usage:** Implement the **Facade/Orchestrator** pattern via a `DataReader` class.
* **Inheritance Requirement:** Every specific data entity (e.g., `Bom`, `Production`) MUST be its own class in its own file and inherit from a central `Base` class (located in `helpers.py`).
* **Base Class Responsibilities:** Handles shared logic: `__init__` initializes `self.data = pl.DataFrame()`; `read()` provides standard reading methods.
* **Entity Responsibilities:** Handle dataset-specific cleaning (`clean()`) and logic. MUST call `super().__init__()`.
* **Orchestrator (`DataReader`):**
    * Instantiates all individual entity classes as attributes in `__init__`.
    * Manages strict sequence: `Read` -> `Clean` -> `Merge/Transform` -> `Write Processed`.
    * Dependency injection happens exclusively in `DataReader.clean()`.
* **Output:** `DataReader` writes cleaned intermediate datasets as **Parquet** files (`.write_parquet()`) to the processed data folder. (Do NOT use CSVs to preserve Polars data types).

---

## 🧪 8. Testing Standards
* **Framework:** Use `pytest`, adhering to a classes-first structure.
* **Design Pattern:** Strictly follow the AAA pattern (Arrange, Act, Assert).
* **Hermetic Testing:** Tests MUST have zero network or AWS dependencies. 
* **Mocking:** Use `moto` for AWS mocking and `pytest-mock` for API mocking.
* **Credentials:** Force dummy AWS credentials in `conftest.py`.

---

## 🌿 9. Git Workflow
* **Commits:** Strictly use Conventional Commits (e.g., `feat:`, `fix:`, `chore:`). Avoid redundant `git status` or `git diff` checks in terminal commands.
* **Branching:** Follow GitFlow conventions. Branch prefixes MUST be `feature/` or `fix/`, originating from the `development` branch.
