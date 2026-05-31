
## 2024-05-18 - Fix focus trapping in QTextEdit
**Learning:** `QTextEdit` traps the Tab key by default for internal navigation or tab character insertion. In form contexts (like the Settings system prompt), this breaks keyboard accessibility because users cannot tab to the next field.
**Action:** Always apply `setTabChangesFocus(True)` to `QTextEdit` widgets used in forms to ensure users can navigate out of the text area using the keyboard.

## 2024-05-27 - Keyboard mnemonics in forms
**Learning:** In PyQt, adding an ampersand (`&`) to a `QLabel` text combined with `setBuddy(widget)` automatically provides a native Alt+Letter keyboard shortcut that focuses the buddy widget. This is highly beneficial for screen reader and power users navigating forms.
**Action:** Consistently use ampersands in label strings and ensure `setBuddy()` is called on all form labels to enhance keyboard accessibility.

## 2024-05-28 - Clean accessible names in forms
**Learning:** When adding `.setAccessibleName()` to form inputs in PyQt6 to match their visual labels, including UI punctuation (like `:`) or keyboard shortcut indicators (like `&`) in the accessible name causes screen readers to unnecessarily vocalize them, leading to a clunky UX.
**Action:** Always strip keyboard shortcut indicators and trailing punctuation when setting `.setAccessibleName()` on form inputs based on their labels.
