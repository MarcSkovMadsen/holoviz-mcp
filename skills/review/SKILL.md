# Review

## Purpose
Perform a `git diff` from the PR branch to the main branch, and review the code changes for potential issues, improvements, and adherence to best practices. Then provide a plan, pointing to lines of code and modules for refactoring the code to improve its quality, readability, and maintainability.

## Checklist
- [ ] DO avoid using `hasattr` and `getattr` when the attribute is known to be present.
- [ ] DO apply `try`/`except` only to the clause that may raise the exception, not to the whole function.
- [ ] DO pin the exception type in the `except` clause; DON'T use a bare `except`.
- [ ] DO return or continue early to avoid deep nesting.
- [ ] DO refactor code with more than three levels of nesting into helper functions.
- [ ] DO place imports at the top of the file; DON'T place imports inside functions unless there is a specific reason (slow import, circular import, etc.).
- [ ] DO consider the full set of changes and whether there is a more efficient or cleaner way to achieve the same result.
- [ ] DO use consistent and readable naming conventions, e.g., if `FollowUpSuggestion` is used, the variable name should be `follow_up_suggestion`, not `followup_suggestion` or `follow_up_suggestions` (plural)
- [ ] if necessary, ensure the feature or enhancement documented in the docs
- [ ] avoid implicit boolean checks on pandas objects, e.g. `if df`, `if df == obj`, etc
