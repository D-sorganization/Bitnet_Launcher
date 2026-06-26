## 2024-06-18 - Added Explicit border-color For Disabled QPushButtons
**Learning:** In Qt/PyQt6, simply setting `color` on a `QPushButton:disabled` selector is insufficient if the button has custom borders. The disabled button will inherit the active-state border color, making it look interactive despite being disabled.
**Action:** Always comprehensively override visual properties (e.g., both `color` and `border-color`) in the `:disabled` pseudo-class for buttons that have custom border styling.

## 2026-06-19 - Added outline: none; to QListWidget:focus
**Learning:** In PyQt6, setting a custom border on an active focus element (like `QListWidget:focus`) does not automatically disable the OS's native dotted focus ring, which causes them to overlap and creates a 'double focus' effect.
**Action:** Always include `outline: none;` in the `:focus` selector alongside any custom `border` definitions in Qt stylesheets.

## 2024-06-20 - Made QLabels Selectable For Copying File Paths
**Learning:** By default, `QLabel` in PyQt6 does not allow users to select text. For informational text such as file paths or repository IDs in detail panes, this is frustrating because users often need to copy this information.
**Action:** Always apply `setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)` to `QLabel` widgets that display important metadata like paths, URLs, or IDs.

## 2024-06-21 - Added Tooltips To Associated QLabels
**Learning:** In Qt/PyQt, adding tooltips to input widgets (e.g., `QSpinBox`, `QLineEdit`) is common, but users often hover over the associated text label (`QLabel`) expecting an explanation of the field, particularly for technical settings or jargon.
**Action:** When a form control has a tooltip and an associated `QLabel` (especially one linked via `setBuddy`), always apply the same tooltip string to the label to increase the discoverable hover area for help text.
