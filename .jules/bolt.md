## 2024-05-30 - Faster import checking

**Learning:** `importlib.import_module()` is significantly slower than `importlib.util.find_spec()` for checking if a module exists, as it fully loads the module rather than just checking if it is available.
**Action:** Use `importlib.util.find_spec()` when we only need to check module availability, like in `check_installation()`.

## 2026-04-22 - PyQt6 QLineEdit Debouncing

**Learning:** In PyQt6, connecting a `QLineEdit.textChanged` signal directly to a heavy sync operation (like table clearing + disk I/O) on every keystroke causes significant main-thread lag. Dropping the text argument by connecting directly to `QTimer.start()` works seamlessly.
**Action:** Use a single-shot `QTimer` to debounce input signals when filtering lists or executing search queries.

## 2026-04-23 - Faster directory traversal with os.scandir

**Learning:** `pathlib.Path.iterdir()` combined with `.glob()` and `.stat()` is slow for directory traversal because it instantiates `Path` objects and performs separate `stat()` system calls.
**Action:** Use `os.scandir()` which is significantly faster (~4-5x) because it yields `os.DirEntry` objects that cache `stat()` results (like `is_dir()`, `is_file()`, and file sizes) on most operating systems, reducing disk I/O.

## 2026-04-26 - PyQt6 object instantiation and disk I/O in loops

**Learning:** Instantiating `QFont` or `QColor` in frequent UI update loops (e.g. `_refresh_table` when searching) is slow. Also, synchronous `Path.exists()` calls within main thread UI loops cause micro-stutters when populating large tables.
**Action:** Cache Qt objects (`QFont`, `QColor`) outside loops and use memory caches (e.g., dict cache or `lru_cache`) for disk I/O status checks in UI callbacks.

## 2024-05-18 - Avoid repeated QColor instantiations in frequent UI updates

**Learning:** In PyQt, instantiating `QColor` (and potentially other Qt objects) repeatedly inside frequently called methods (like `append_assistant` during LLM text streaming) creates measurable overhead and can cause UI micro-stutters.
**Action:** Cache these objects as instance variables during initialization (`__init__`) and reuse them across calls to eliminate the object creation overhead in the hot path.

## 2024-06-05 - PyQt6 QTableWidget bulk updates

**Learning:** Repopulating a `QTableWidget` without disabling updates causes synchronous layout recalculations and repaints for every single `setItem` call. This creates a significant performance bottleneck and blocks the main thread during batch insertions, especially when recreating the entire table inside a search filter callback.
**Action:** Always wrap `QTableWidget` batch updates with `setUpdatesEnabled(False)` and `setUpdatesEnabled(True)` to defer layout recalculations until all items have been inserted.

## 2026-04-22 - PyQt6 QLineEdit Debouncing

**Learning:** In PyQt6, connecting a `QLineEdit.textChanged` signal directly to a heavy sync operation (like table clearing + disk I/O) on every keystroke causes significant main-thread lag. Dropping the text argument by connecting directly to `QTimer.start()` works seamlessly.
**Action:** Use a single-shot `QTimer` to debounce input signals when filtering lists or executing search queries.

## 2024-05-13 - PyQt6 QListWidget bulk updates

**Learning:** Adding items to a `QListWidget` in a loop inside `_build_ui` triggers synchronous layout recalculations and repaints for every cell.
**Action:** Use `setUpdatesEnabled(False)` and `setUpdatesEnabled(True)` around `QListWidget` bulk item insertions.

## 2024-05-23 - Remove synchronous Path.exists() check from \_refresh_table

**Learning:** `Path.exists()` operations running inside `_refresh_table` triggered by user keystrokes cause main thread lag and UI stutter, especially in loops or frequently called filter functions. Since the existence of an environment file `setup_env.py` is unlikely to change during the lifetime of a specific modal dialog, repeatedly checking it inside a dynamic search filter is inefficient.
**Action:** Remove redundant `Path.exists()` checks from frequent UI callbacks if the boolean value has already been evaluated and cached during `__init__`.

## 2024-05-30 - Context Managers for os.scandir()

**Learning:** When using `os.scandir()` with short-circuiting iterators (like `any()` or `all()`), breaking early leaves the generator unexhausted. Relying on CPython's garbage collector to close the underlying directory file descriptor is risky and discouraged in production code.
**Action:** Always wrap `os.scandir(path)` in a `with` context manager (e.g., `with os.scandir(path) as it:`) when the iteration might not consume all elements, ensuring explicit and safe cleanup of file handles.
## 2024-06-25 - Avoid redundant string evaluations in tight loops
**Learning:** Calling `.lower()` multiple times in a generator expression on the same string (e.g. `any(f.name.lower().endswith(".gguf") and "tq2_0" in f.name.lower())`) causes redundant string allocations and method calls per iteration.
**Action:** Use the walrus operator (`:=`) inside generator expressions to compute the value once and reuse it: `any((lname := f.name.lower()).endswith(".gguf") and "tq2_0" in lname)`.
