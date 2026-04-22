## 2023-10-27 - PyQt6 Standalone Input Accessibility
**Learning:** In PyQt6, `QLineEdit` and `QTextEdit` widgets that do not have a corresponding `QLabel` associated via `setBuddy()` are silent or generic to screen readers.
**Action:** Always use `setAccessibleName()` on standalone input fields and read-only text areas (like search bars or chat displays) to ensure screen readers can announce their purpose correctly.
