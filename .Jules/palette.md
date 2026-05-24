
## 2024-05-18 - Fix focus trapping in QTextEdit
**Learning:** `QTextEdit` traps the Tab key by default for internal navigation or tab character insertion. In form contexts (like the Settings system prompt), this breaks keyboard accessibility because users cannot tab to the next field.
**Action:** Always apply `setTabChangesFocus(True)` to `QTextEdit` widgets used in forms to ensure users can navigate out of the text area using the keyboard.
