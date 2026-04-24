## 2024-05-30 - Faster import checking
**Learning:** `importlib.import_module()` is significantly slower than `importlib.util.find_spec()` for checking if a module exists, as it fully loads the module rather than just checking if it is available.
**Action:** Use `importlib.util.find_spec()` when we only need to check module availability, like in `check_installation()`.

## 2026-04-22 - PyQt6 QLineEdit Debouncing
**Learning:** In PyQt6, connecting a `QLineEdit.textChanged` signal directly to a heavy sync operation (like table clearing + disk I/O) on every keystroke causes significant main-thread lag. Dropping the text argument by connecting directly to `QTimer.start()` works seamlessly.
**Action:** Use a single-shot `QTimer` to debounce input signals when filtering lists or executing search queries.

## 2026-04-23 - Faster directory traversal with os.scandir
**Learning:** `pathlib.Path.iterdir()` combined with `.glob()` and `.stat()` is slow for directory traversal because it instantiates `Path` objects and performs separate `stat()` system calls.
**Action:** Use `os.scandir()` which is significantly faster (~4-5x) because it yields `os.DirEntry` objects that cache `stat()` results (like `is_dir()`, `is_file()`, and file sizes) on most operating systems, reducing disk I/O.

## 2024-06-25 - PyQt6 QTableWidget Repopulation Lag
**Learning:** Repopulating a `QTableWidget` without pausing updates (`setUpdatesEnabled(False)`) causes expensive sequential layout recalculations and repaints for every cell insertion. Even with debouncing, rendering many rows synchronously on the main thread will stutter.
**Action:** Always wrap bulk updates to `QTableWidget` items inside a `try...finally` block with `setUpdatesEnabled(False)` before and `setUpdatesEnabled(True)` after.
