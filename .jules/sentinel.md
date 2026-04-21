## 2024-04-21 - [Fix Command Injection in Terminal Launcher]
**Vulnerability:** A command injection vulnerability existed in `src/bitnet_launcher/terminal.py` where the system prompt (controlled by the user) was naive string-concatenated with quotes into a shell command using `" ".join(f'"{part}"' if " " in part else part for part in cmd)`.
**Learning:** Naive shell quoting logic doesn't properly escape characters like double quotes or semicolons inside the user-provided string, allowing for command injection.
**Prevention:** Use Python's built-in `shlex.join(cmd)` instead of manually creating shell quotes when constructing arguments for a shell command.
