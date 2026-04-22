## 2024-05-30 - Faster import checking
**Learning:** `importlib.import_module()` is significantly slower than `importlib.util.find_spec()` for checking if a module exists, as it fully loads the module rather than just checking if it is available.
**Action:** Use `importlib.util.find_spec()` when we only need to check module availability, like in `check_installation()`.

## 2026-04-22 - PyQt6 QLineEdit Debouncing
**Learning:** In PyQt6, connecting a `QLineEdit.textChanged` signal directly to a heavy sync operation (like table clearing + disk I/O) on every keystroke causes significant main-thread lag. Dropping the text argument by connecting directly to `QTimer.start()` works seamlessly.
**Action:** Use a single-shot `QTimer` to debounce input signals when filtering lists or executing search queries.
