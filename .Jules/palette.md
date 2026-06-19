## 2024-06-18 - Added Explicit border-color For Disabled QPushButtons
**Learning:** In Qt/PyQt6, simply setting `color` on a `QPushButton:disabled` selector is insufficient if the button has custom borders. The disabled button will inherit the active-state border color, making it look interactive despite being disabled.
**Action:** Always comprehensively override visual properties (e.g., both `color` and `border-color`) in the `:disabled` pseudo-class for buttons that have custom border styling.

## 2026-06-19 - Added outline: none; to QListWidget:focus
**Learning:** In PyQt6, setting a custom border on an active focus element (like `QListWidget:focus`) does not automatically disable the OS's native dotted focus ring, which causes them to overlap and creates a 'double focus' effect.
**Action:** Always include `outline: none;` in the `:focus` selector alongside any custom `border` definitions in Qt stylesheets.
