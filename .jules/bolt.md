## 2025-02-18 - [Optimize Generator Comprehension]
**Learning:** In Python generator expressions or comprehensions, using the walrus operator (`:=`) to cache the result of an expensive string operation (like `f.lower()`) prevents redundant method calls and string allocations per iteration when the result is needed multiple times in the same condition.
**Action:** Use the walrus operator (`:=`) to assign expensive string operations to a local variable if it needs to be evaluated multiple times in the same condition.
