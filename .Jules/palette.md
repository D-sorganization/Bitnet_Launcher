## 2024-06-18 - Added Explicit border-color For Disabled QPushButtons
**Learning:** In Qt/PyQt6, simply setting `color` on a `QPushButton:disabled` selector is insufficient if the button has custom borders. The disabled button will inherit the active-state border color, making it look interactive despite being disabled.
**Action:** Always comprehensively override visual properties (e.g., both `color` and `border-color`) in the `:disabled` pseudo-class for buttons that have custom border styling.
