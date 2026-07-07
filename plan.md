1. **Fix DoS vulnerability by limiting concurrent runners in the global registry**
   - In `src/bitnet_launcher/api.py`, update `active_runners` typing to allow `None` values (i.e., `dict[str, LocalLlamaRunner | None]`).
   - In the `/chat/start` endpoint, implement early return checking if `request.model_name in active_runners` to prevent concurrent duplicate model starts (returns 409).
   - Implement an overall concurrency limit (returns 429) to restrict concurrent resource allocation (e.g., if `len(active_runners) >= 1`).
   - Claim the runner's slot synchronously with a placeholder (`active_runners[request.model_name] = None`) *before* spawning the `runner.start()` coroutine.

2. **Add unit tests verifying behavior**
   - In `tests/unit/test_api.py`, add `test_start_chat_already_running` to verify starting the same model returns 409.
   - Add `test_start_chat_concurrency_limit` to verify starting a second model returns 429.
   - Ensure `test_start_chat_success` handles the registry clearance to avoid state leakage between tests.

3. **Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.**
   - Run code formatter and linter (`uv run ruff format src/ tests/`, `uv run ruff check src/ tests/`).
   - Run tests (`QT_QPA_PLATFORM=offscreen uv run pytest tests/unit/ -q -p no:xvfb`).
   - Check journal and rules alignment.

4. **Submit changes via pull request**
   - Create PR addressing Sentinel task with `CRITICAL/HIGH` severity tag and relevant documentation in PR description.
