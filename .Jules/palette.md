## 2024-06-18 - Added Explicit border-color For Disabled QPushButtons
**Learning:** In Qt/PyQt6, simply setting `color` on a `QPushButton:disabled` selector is insufficient if the button has custom borders. The disabled button will inherit the active-state border color, making it look interactive despite being disabled.
**Action:** Always comprehensively override visual properties (e.g., both `color` and `border-color`) in the `:disabled` pseudo-class for buttons that have custom border styling.

## 2026-06-19 - Added outline: none; to QListWidget:focus
**Learning:** In PyQt6, setting a custom border on an active focus element (like `QListWidget:focus`) does not automatically disable the OS's native dotted focus ring, which causes them to overlap and creates a 'double focus' effect.
**Action:** Always include `outline: none;` in the `:focus` selector alongside any custom `border` definitions in Qt stylesheets.

## 2024-06-20 - Made QLabels Selectable For Copying File Paths
**Learning:** By default, `QLabel` in PyQt6 does not allow users to select text. For informational text such as file paths or repository IDs in detail panes, this is frustrating because users often need to copy this information.
**Action:** Always apply `setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)` to `QLabel` widgets that display important metadata like paths, URLs, or IDs.

## 2026-06-21 - Enforced SingleSelection for Tables with Single-Target Actions
**Learning:** In PyQt6 `QTableWidget`s, if the primary action (like downloading a model or editing a single entry) only supports operating on one item at a time, allowing multiple selection (the default) confuses users. They might select multiple rows and wonder why only one was affected.
**Action:** Always explicitly restrict tables to single-row selection using `setSelectionMode(QTableWidget.SelectionMode.SingleSelection)` when the associated action does not support bulk operations.
## 2026-06-21 - Disabled related configuration inputs during async operations in PyQt
**Learning:** In PyQt applications, when a long-running asynchronous operation (like a download) is triggered, leaving related input widgets (like search bars or filter dropdowns) enabled can lead to unexpected state changes or confused users.
**Action:** Always disable all related configuration input widgets simultaneously when disabling the primary action button, update their tooltips to explain the disabled state (e.g., 'An operation is currently in progress'), and ensure they are all properly re-enabled and their tooltips restored in both success and error completion handlers.
