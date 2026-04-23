## 2023-10-27 - PyQt6 Standalone Input Accessibility
**Learning:** In PyQt6, `QLineEdit` and `QTextEdit` widgets that do not have a corresponding `QLabel` associated via `setBuddy()` are silent or generic to screen readers.
**Action:** Always use `setAccessibleName()` on standalone input fields and read-only text areas (like search bars or chat displays) to ensure screen readers can announce their purpose correctly.
## 2025-01-28 - Dynamic Tooltips for Disabled Buttons
**Learning:** In PyQt6, disabling a button (`setEnabled(False)`) makes it unresponsive, but a tooltip can still be displayed if hovered, which is crucial for explaining *why* an action is unavailable (e.g., "Model already installed" or "Download in progress").
**Action:** When conditionally disabling a button, always update its `setToolTip()` string to provide context instead of leaving the user guessing.
