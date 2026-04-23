## 2024-04-21 - [Fix Command Injection in Terminal Launcher]
**Vulnerability:** A command injection vulnerability existed in `src/bitnet_launcher/terminal.py` where the system prompt (controlled by the user) was naive string-concatenated with quotes into a shell command using `" ".join(f'"{part}"' if " " in part else part for part in cmd)`.
**Learning:** Naive shell quoting logic doesn't properly escape characters like double quotes or semicolons inside the user-provided string, allowing for command injection.
**Prevention:** Use Python's built-in `shlex.join(cmd)` instead of manually creating shell quotes when constructing arguments for a shell command.
## 2026-04-23 - [Command Injection Risk via Terminal Launch]
**Vulnerability:** In `src/bitnet_launcher/terminal.py`, `bitnet_root` is enclosed in double quotes during bash command construction (e.g., `f'cd "{bitnet_root}" && ...'`). An attacker or unexpected path could contain double quotes and bash meta-characters, leading to command injection.
**Learning:** Constructing bash commands by string concatenation—even using double quotes—can fail securely if the parameter contains double quotes or backticks. Always use `shlex.quote()` to safely escape arbitrary paths in a shell context.
**Prevention:** Use `shlex.quote(str(path))` instead of `f'"{path}"'` when injecting into a bash `-c` string.
