# Review

## Purpose
Perform a `git diff` from the PR branch to the main branch, and review the code changes for potential issues, improvements, and adherence to best practices. Then provide a plan, pointing to lines of code and modules for refactoring the code to improve its quality, readability, and maintainability.

## Checklist
- [ ] when the attribute is known to be present, do not use `hasattr` & `getattr`
- [ ] use try/except only on the clause that may raise the exception, not on the whole function
- [ ] try to pin the exception type in the except clause, do not use a bare except
- [ ] return or continue early to avoid deep nesting
- [ ] anything over 3 levels of nesting should be refactored into helper functions
- [ ] imports should be at the top of the file, not inside functions unless there is a specific reason to do so (slow import, circular import, etc.)
- [ ] understanding the full changes, is there a more efficient or cleaner way to achieve the same result?
- [ ] consistent and readable naming conventions, e.g. if FollowUpSuggestion is used, the variable name should be follow_up_suggestion, not followup_suggestion or follow_up_suggestions (plural)
- [ ] if necessary, ensure the feature or enhancement documented in the docs
- [ ] avoid implicit boolean checks on pandas objects, e.g. `if df`, `if df == obj`, etc
