"""
Example Parameterized classes for testing the param-lsp server.

Open this file in VS Code with the param-lsp extension active to see:
- Hover documentation for param declarations
- Autocompletion for param types after "param."
- Autocompletion for kwargs inside param.Type(...)
- Autocompletion for parameter names when instantiating classes
- Diagnostics for unknown types and missing required kwargs
"""

import param


class Person(param.Parameterized):
    """A person with various attributes."""

    name = param.String(default="Anonymous", doc="The person's name")
    age = param.Integer(default=0, bounds=(0, 150), doc="Age in years")
    height = param.Number(default=1.7, bounds=(0.0, 3.0), doc="Height in meters")
    is_active = param.Boolean(default=True, doc="Whether the person is active")
    email = param.String(default="", regex=r"^[\w\.-]+@[\w\.-]+\.\w+$", doc="Email address")


class Employee(Person):
    """An employee extending Person."""

    employee_id = param.String(doc="Unique employee identifier")
    department = param.Selector(
        objects=["Engineering", "Sales", "Marketing", "HR"],
        default="Engineering",
        doc="Department the employee belongs to",
    )
    salary = param.Number(default=50000, bounds=(0, None), doc="Annual salary")
    skills = param.List(default=[], item_type=str, doc="List of skills")


class Project(param.Parameterized):
    """A project with team members."""

    name = param.String(default="Untitled", doc="Project name")
    lead = param.ClassSelector(class_=Employee, doc="Project lead")
    team = param.List(default=[], item_type=Employee, doc="Team members")
    budget = param.Number(default=0, bounds=(0, None), doc="Project budget")
    status = param.Selector(
        objects=["Planning", "In Progress", "Review", "Complete"],
        default="Planning",
        doc="Current project status",
    )
    start_date = param.Date(doc="Project start date")
    config = param.Dict(default={}, doc="Additional configuration")


class DataProcessor(param.Parameterized):
    """A data processing pipeline."""

    input_path = param.Path(doc="Input file or folder path")
    output_path = param.Filename(doc="Output filename")
    batch_size = param.Integer(default=100, bounds=(1, 10000), doc="Processing batch size")
    threshold = param.Number(default=0.5, bounds=(0.0, 1.0), doc="Decision threshold")
    on_complete = param.Callable(doc="Callback when processing is complete")
    verbose = param.Boolean(default=False, doc="Enable verbose logging")


# Example instantiation - the LSP should provide completion for parameter names
if __name__ == "__main__":
    # Try typing inside the parentheses to see completions
    person = Person(
        name="Alice",
        age=30,
    )

    employee = Employee(
        name="Bob",
        department="Engineering",
        skills=["Python", "Data Science"],
    )

    print(f"Person: {person.name}, {person.age} years old", person.email)
    print(f"Employee: {employee.name}, {employee.department}")

Person()
