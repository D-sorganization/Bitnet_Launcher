
## 2024-05-18 - Fix focus trapping in QTextEdit
**Learning:** `QTextEdit` traps the Tab key by default for internal navigation or tab character insertion. In form contexts (like the Settings system prompt), this breaks keyboard accessibility because users cannot tab to the next field.
**Action:** Always apply `setTabChangesFocus(True)` to `QTextEdit` widgets used in forms to ensure users can navigate out of the text area using the keyboard.

## 2024-05-27 - Keyboard mnemonics in forms
**Learning:** In PyQt, adding an ampersand (`&`) to a `QLabel` text combined with `setBuddy(widget)` automatically provides a native Alt+Letter keyboard shortcut that focuses the buddy widget. This is highly beneficial for screen reader and power users navigating forms.
**Action:** Consistently use ampersands in label strings and ensure `setBuddy()` is called on all form labels to enhance keyboard accessibility.

## 2024-05-28 - Clean accessible names in forms
**Learning:** When adding `.setAccessibleName()` to form inputs in PyQt6 to match their visual labels, including UI punctuation (like `:`) or keyboard shortcut indicators (like `&`) in the accessible name causes screen readers to unnecessarily vocalize them, leading to a clunky UX.
**Action:** Always strip keyboard shortcut indicators and trailing punctuation when setting `.setAccessibleName()` on form inputs based on their labels.

## 2024-06-02 - List and table item double-click actions
**Learning:** In PyQt6 desktop applications, requiring users to select an item from a list or table and then move the mouse to click a separate primary action button (like "Download" or "Chat Here") creates a disjointed interaction flow.
**Action:** Enhance list and table interactions by connecting the `itemDoubleClicked` signal to the primary action, providing a standard desktop shortcut alongside traditional action buttons.

## 2024-06-10 - Missing focus styles on QComboBox
**Learning:** In PyQt6 custom stylesheets, it's easy to overlook `QComboBox` when defining `:focus` styles for text inputs (`QLineEdit`, `QTextEdit`, `QSpinBox`). Without explicit `:focus` rules, `QComboBox` lacks visual indicators when receiving keyboard focus, breaking accessibility.
**Action:** Always include `QComboBox` and `QComboBox:focus` alongside standard text input selectors in Qt stylesheets to ensure uniform keyboard navigation feedback.

## 2024-06-11 - Keyboard activation for list and table items
**Learning:** In PyQt6, connecting only to `itemDoubleClicked` on `QListWidget` or `QTableWidget` limits the shortcut action to mouse users. Keyboard users who navigate to an item and press Enter will not trigger the action.
**Action:** Use the `itemActivated` signal instead of `itemDoubleClicked`. `itemActivated` is triggered by both mouse double-clicks and the Enter/Return key, ensuring feature parity and full accessibility for keyboard users.
