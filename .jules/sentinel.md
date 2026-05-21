## 2024-04-21 - [Fix Command Injection in Terminal Launcher]

**Vulnerability:** A command injection vulnerability existed in `src/bitnet_launcher/terminal.py` where the system prompt (controlled by the user) was naive string-concatenated with quotes into a shell command using `" ".join(f'"{part}"' if " " in part else part for part in cmd)`.
**Learning:** Naive shell quoting logic doesn't properly escape characters like double quotes or semicolons inside the user-provided string, allowing for command injection.
**Prevention:** Use Python's built-in `shlex.join(cmd)` instead of manually creating shell quotes when constructing arguments for a shell command.

## 2026-04-23 - [Command Injection Risk via Terminal Launch]

**Vulnerability:** In `src/bitnet_launcher/terminal.py`, `bitnet_root` is enclosed in double quotes during bash command construction (e.g., `f'cd "{bitnet_root}" && ...'`). An attacker or unexpected path could contain double quotes and bash meta-characters, leading to command injection.
**Learning:** Constructing bash commands by string concatenation—even using double quotes—can fail securely if the parameter contains double quotes or backticks. Always use `shlex.quote()` to safely escape arbitrary paths in a shell context.
**Prevention:** Use `shlex.quote(str(path))` instead of `f'"{path}"'` when injecting into a bash `-c` string.

## 2025-02-17 - Prevent XSS/HTML Injection in QTextEdit

**Vulnerability:** Untrusted string input was appended to `QTextEdit` via the `append()` method, which natively parses and renders HTML, leading to potential Cross-Site Scripting (XSS) and Rich Text injection.
**Learning:** `QTextEdit.append()` accepts HTML and applies parsing. When dealing with untrusted user text or logs, it will render HTML tags unless the content is strictly plain text only. This behavior is dangerous when handling inputs directly from users, models, or system logs.
**Prevention:** Use `insertPlainText()` along with cursor manipulation (moving cursor to end and inserting a newline) rather than `append()` to ensure all content is strictly treated as text.

## 2025-03-01 - Prevent HTML Injection in QLabel via AutoText

**Vulnerability:** `QLabel` objects initialized with untrusted text (like `QLabel("...")` or `setText()`) can automatically render HTML if the text looks like HTML or if the text format is set to `AutoText` (the default). If a model name or user input containing HTML tags is displayed in a status label, this could lead to Rich Text injection or UI redressing.
**Learning:** In PyQt applications, `QLabel` uses `Qt.TextFormat.AutoText` by default, which heuristically parses text. Any widget accepting raw user data to display must be explicitly forced into plain text mode if it doesn't need to support HTML styling.
**Prevention:** Always use `.setTextFormat(Qt.TextFormat.PlainText)` on `QLabel` instances that display dynamic, untrusted text.

## 2025-03-01 - Prevent HTML Injection in rich text QLabel

**Vulnerability:** In `src/bitnet_launcher/gui/hub_dialog.py`, dynamic external properties (`model.name`, `model.description`, `model.repo_id`) were directly formatted into a rich-text HTML string inside a `QLabel`, leading to potential Cross-Site Scripting (XSS) and HTML injection if the Hugging Face catalog contained malicious characters.
**Learning:** In PyQt6, when a `QLabel` requires rich text formatting (using tags like `<b>` or `<br>`), you cannot simply use `Qt.TextFormat.PlainText`. Thus, any untrusted dynamic data injected into the string must be manually escaped.
**Prevention:** Always use `html.escape()` on dynamic values before interpolating them into a string that will be evaluated as HTML by a `QLabel`.

## 2025-03-01 - Prevent HTML Injection in QMessageBox

**Vulnerability:** `QMessageBox` text automatically evaluates HTML by default if it looks like HTML (similar to `QLabel`). If user input (like error messages, shell commands, or arbitrary paths) contains HTML tags, it will be rendered as rich text. This leads to Rich Text injection or UI redressing if input is not sanitized or escaped.
**Learning:** `QMessageBox` text should never directly concatenate untrusted input unless it's escaped or unless the dialog is explicitly configured not to interpret rich text. However, `QMessageBox.critical` and other static methods don't support passing `Qt.TextFormat`.
**Prevention:** Instead of using the static convenience methods (`QMessageBox.critical()`, etc.), instantiate a `QMessageBox` object and explicitly call `setTextFormat(Qt.TextFormat.PlainText)` before setting the text and executing.

## 2026-05-03 - Prevent HTML Injection in QMessageBox

**Vulnerability:** `QMessageBox` text automatically evaluates HTML by default if it looks like HTML. If user input (like error messages, shell commands, or arbitrary paths) contains HTML tags, it will be rendered as rich text. This leads to Rich Text injection or UI redressing if input is not sanitized or escaped.
**Learning:** `QMessageBox` text should never directly concatenate untrusted input unless it's escaped or unless the dialog is explicitly configured not to interpret rich text. However, `QMessageBox.critical` and other static methods don't support passing `Qt.TextFormat`.
**Prevention:** Instead of using the static convenience methods (`QMessageBox.critical()`, etc.), instantiate a `QMessageBox` object and explicitly call `setTextFormat(Qt.TextFormat.PlainText)` before setting the text and executing.
## 2025-03-01 - [Prevent HTML Injection in rich text QLabel using dynamic properties]

**Vulnerability:** Untrusted dynamic fields (like `model.params`) from external sources were interpolated into rich text `QLabel` strings without being escaped.
**Learning:** `QLabel` will interpret any interpolated string as HTML if tags are present. If you cannot use `Qt.TextFormat.PlainText` because the label structurally requires rich text (e.g. `<b>`, `<br>`), you must individually escape every dynamic external property.
**Prevention:** Always use `html.escape()` on string-cast properties before inserting them into a rich text `QLabel`.
