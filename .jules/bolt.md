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

## 2024-06-25 - FastAPI Async Endpoints and Disk I/O Blocking

**Learning:** In FastAPI `async def` endpoints, directly calling synchronous functions that perform blocking disk I/O (like `os.scandir` in `discover_models`) blocks the asyncio event loop.
**Action:** Always wrap synchronous disk I/O calls in `await asyncio.to_thread()` to offload them to a thread pool and keep the main event loop responsive.

## 2024-06-25 - Concurrency Limits and Race Conditions in Async Registries

**Learning:** Enforcing concurrency limits via a global registry in async FastAPI endpoints (like `active_runners`) is susceptible to race conditions. If multiple parallel requests check the limit before any of them hit an `await` (which yields control back to the event loop), they can all bypass the limit.
**Action:** Immediately insert a placeholder entry (e.g., `registry[key] = None`) into the dictionary *after* the limit check and *before* any `await` or blocking operations to secure the concurrency slot synchronously. Furthermore, check `if registry[key] is None` to reject duplicate pending requests for the same resource.

## 2024-06-25 - Clean up Async Registries with BaseException

**Learning:** In modern Python (3.8+), Uvicorn raises `asyncio.CancelledError` on client disconnects, which inherits from `BaseException`, not `Exception`. If a resource initialization is cancelled and wrapped in a standard `except Exception:` block, the cleanup will be bypassed.
**Action:** When cleaning up async state locks or placeholders (e.g., popping from `active_runners`), use `except BaseException:` or `finally` blocks to guarantee cleanup and prevent permanent resource leaks if a request is aborted.
