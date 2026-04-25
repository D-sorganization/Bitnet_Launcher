## 2024-05-30 - Faster import checking
**Learning:** `importlib.import_module()` is significantly slower than `importlib.util.find_spec()` for checking if a module exists, as it fully loads the module rather than just checking if it is available.
**Action:** Use `importlib.util.find_spec()` when we only need to check module availability, like in `check_installation()`.

## 2026-04-22 - PyQt6 QLineEdit Debouncing
**Learning:** In PyQt6, connecting a `QLineEdit.textChanged` signal directly to a heavy sync operation (like table clearing + disk I/O) on every keystroke causes significant main-thread lag. Dropping the text argument by connecting directly to `QTimer.start()` works seamlessly.
**Action:** Use a single-shot `QTimer` to debounce input signals when filtering lists or executing search queries.

## 2026-04-23 - Faster directory traversal with os.scandir
**Learning:** `pathlib.Path.iterdir()` combined with `.glob()` and `.stat()` is slow for directory traversal because it instantiates `Path` objects and performs separate `stat()` system calls.
**Action:** Use `os.scandir()` which is significantly faster (~4-5x) because it yields `os.DirEntry` objects that cache `stat()` results (like `is_dir()`, `is_file()`, and file sizes) on most operating systems, reducing disk I/O.
## 2024-04-25 - Cache Qt Object Creation in Loops
**Learning:** Instantiating `QColor` or `QFont` objects inside loops (like `_refresh_table`) in PyQt can be surprisingly slow, especially when string parsing is involved (e.g., `QColor("#a6e3a1")`).
**Action:** When populating tables or lists with many items, cache unchanging Qt objects (`QColor`, `QFont`, etc.) outside the loop to avoid recreating them for every item.

## 2024-04-25 - Avoid Main-Thread Disk I/O in UI Filters
**Learning:** Checking `Path.exists()` for each table row during a filter operation (like typing in a search box) causes unpredictable main-thread blocking, leading to UI micro-stutters even if the search input is debounced.
**Action:** Cache the results of filesystem checks (e.g., in a `set` during initialization or after explicit updates) and query the cache during UI refresh operations instead of hitting the disk.
