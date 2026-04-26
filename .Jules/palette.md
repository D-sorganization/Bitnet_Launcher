## 2023-10-27 - PyQt6 Standalone Input Accessibility
**Learning:** In PyQt6, `QLineEdit` and `QTextEdit` widgets that do not have a corresponding `QLabel` associated via `setBuddy()` are silent or generic to screen readers.
**Action:** Always use `setAccessibleName()` on standalone input fields and read-only text areas (like search bars or chat displays) to ensure screen readers can announce their purpose correctly.
## 2025-01-28 - Dynamic Tooltips for Disabled Buttons
**Learning:** In PyQt6, disabling a button (`setEnabled(False)`) makes it unresponsive, but a tooltip can still be displayed if hovered, which is crucial for explaining *why* an action is unavailable (e.g., "Model already installed" or "Download in progress").
**Action:** When conditionally disabling a button, always update its `setToolTip()` string to provide context instead of leaving the user guessing.
## 2024-05-24 - Qt Stylesheet Focus Indicators
**Learning:** The app uses a custom Qt stylesheet (Catppuccin) which overrides default OS focus indicators for keyboard navigation, hiding tab focus.
**Action:** Always explicitly add `:focus` pseudo-class rules (e.g. `border: 1px solid {t.ACCENT};`) to interactive UI components when writing or modifying Qt stylesheets to preserve keyboard accessibility.
## 2024-04-26 - Disabled Button Tooltips
**Learning:** When conditionally disabling a button (`setEnabled(False)`), screen reader users or keyboard navigators may still focus on or interact with the space, and the tooltip is still visible on disabled elements. It helps users to know *why* the button is unavailable.
**Action:** Always update the `setToolTip()` string of a button when disabling it to explain the state (e.g., "An operation is currently in progress"), and restore the original tooltip when re-enabling it.
