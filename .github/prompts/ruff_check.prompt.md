When fixing ruff issues, please follow these guidelines below.

Please fix one issue at a time and test the change before progressing to next issue.
Please fix ruff issues in the 'src' and 'tests' folders only.
Please fix easy to fix issues before more complex ones.
For complex ones feel free to ask the user for guidance or help.

## Specific Rules

### D405

Please ensure the docstring change is meaningful to end users and Google style.
If the summary extends to multiple lines please reformulate instead of breaking the summary into two distinct lines.

### ARG001

If the argument is an unused pytest fixture please change it to a marker, e.g. to `@pytest.mark.usefixtures("name_of_fixture")`.
