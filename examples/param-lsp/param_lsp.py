#!/usr/bin/env python
"""
Minimal LSP Server for param - Single File Example

Install dependencies:
    pip install pygls lsprotocol param

Run the server:
    python param_lsp.py

Configure VS Code (settings.json):
    Add to your settings.json to test with a generic LSP client extension
"""

import re

from lsprotocol import types as lsp
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument

# Create the language server
server = LanguageServer("param-lsp", "v0.1.0")

# Map param types to Python types and descriptions
PARAM_TYPE_INFO = {
    "param.Integer": ("int", "Integer parameter with optional bounds"),
    "param.Number": ("float", "Numeric parameter (float) with optional bounds"),
    "param.String": ("str", "String parameter with optional regex validation"),
    "param.Boolean": ("bool", "Boolean parameter (True/False)"),
    "param.List": ("list", "List parameter with optional item type"),
    "param.Dict": ("dict", "Dictionary parameter"),
    "param.Selector": ("Any", "Single selection from a list of objects"),
    "param.ListSelector": ("list", "Multiple selections from a list of objects"),
    "param.ClassSelector": ("object", "Instance or subclass of a specified class"),
    "param.Callable": ("Callable", "Callable object (function, method, etc.)"),
    "param.Action": ("Callable", "Callable with no arguments, ready to invoke"),
    "param.Parameter": ("Any", "Generic parameter"),
    "param.Tuple": ("tuple", "Python tuple of fixed length"),
    "param.Range": ("tuple[float, float]", "Numeric range with optional bounds"),
    "param.Date": ("datetime", "Date or datetime value"),
    "param.Color": ("str", "Hex RGB color string or named color"),
    "param.Path": ("str", "POSIX-style path string"),
    "param.Filename": ("str", "POSIX-style filename string"),
    "param.Foldername": ("str", "POSIX-style folder path string"),
    "param.DataFrame": ("pandas.DataFrame", "Pandas DataFrame"),
    "param.Series": ("pandas.Series", "Pandas Series"),
    "param.Array": ("numpy.ndarray", "NumPy array"),
    "param.Event": ("bool", "Event trigger parameter"),
}

# Regex to find param declarations: name = param.Type(...)
PARAM_PATTERN = re.compile(r"^\s*(\w+)\s*=\s*(param\.(\w+))\s*\(([^)]*)\)", re.MULTILINE)

# Regex to find class definitions inheriting from Parameterized
CLASS_PATTERN = re.compile(r"^class\s+(\w+)\s*\([^)]*(?:param\.)?Parameterized[^)]*\)\s*:", re.MULTILINE)


def parse_param_args(args_str: str) -> dict:
    """Parse parameter arguments from the declaration string."""
    result = {}
    # Simple parsing for common kwargs
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?:,|$)", args_str):
        key, value = match.groups()
        result[key.strip()] = value.strip()
    # Check for positional default (first arg without =)
    first_arg = args_str.split(",")[0].strip() if args_str else ""
    if first_arg and "=" not in first_arg:
        result["default"] = first_arg
    return result


def find_param_at_position(document: TextDocument, position: lsp.Position) -> dict | None:
    """Find the param declaration at the given position."""
    lines = document.source.split("\n")
    if position.line >= len(lines):
        return None

    line = lines[position.line]

    # Check if cursor is on a param declaration line
    match = PARAM_PATTERN.match(line)
    if not match:
        return None

    name, full_type, type_name, args = match.groups()

    # Check if cursor is within the match
    start = match.start()
    end = match.end()
    if not (start <= position.character <= end):
        return None

    return {
        "name": name,
        "param_type": full_type,
        "type_name": type_name,
        "args": parse_param_args(args),
        "line": position.line,
    }


def find_all_params_in_document(document: TextDocument) -> list[dict]:
    """Find all param declarations in the document."""
    params = []
    lines = document.source.split("\n")

    for line_num, line in enumerate(lines):
        match = PARAM_PATTERN.match(line)
        if match:
            name, full_type, type_name, args = match.groups()
            params.append(
                {
                    "name": name,
                    "param_type": full_type,
                    "type_name": type_name,
                    "args": parse_param_args(args),
                    "line": line_num,
                }
            )

    return params


def find_parameterized_classes(document: TextDocument) -> list[dict]:
    """Find all Parameterized class definitions in the document."""
    classes = []
    lines = document.source.split("\n")

    for line_num, line in enumerate(lines):
        match = CLASS_PATTERN.match(line)
        if match:
            class_name = match.group(1)
            # Find parameters belonging to this class (simple heuristic: indented lines after class def)
            class_params = []
            for i in range(line_num + 1, len(lines)):
                param_line = lines[i]
                # Stop at next class or unindented line
                if param_line and not param_line.startswith((" ", "\t")):
                    break
                param_match = PARAM_PATTERN.match(param_line)
                if param_match:
                    name, full_type, type_name, args = param_match.groups()
                    class_params.append(
                        {
                            "name": name,
                            "param_type": full_type,
                            "type_name": type_name,
                            "args": parse_param_args(args),
                            "line": i,
                        }
                    )

            classes.append(
                {
                    "name": class_name,
                    "line": line_num,
                    "params": class_params,
                }
            )

    return classes


# Regex to find variable assignments: var = ClassName(...)
INSTANCE_PATTERN = re.compile(r"^\s*(\w+)\s*=\s*(\w+)\s*\(")

# Regex to find attribute access: var.attr
ATTR_ACCESS_PATTERN = re.compile(r"\b(\w+)\.(\w+)\b")


def find_instance_class(document: TextDocument, var_name: str) -> str | None:
    """Find the class name for a variable assignment like 'person = Person(...)'."""
    for line in document.source.split("\n"):
        match = INSTANCE_PATTERN.match(line)
        if match and match.group(1) == var_name:
            return match.group(2)
    return None


def find_param_for_attribute(document: TextDocument, var_name: str, attr_name: str) -> dict | None:
    """Find param info for an attribute access like 'person.name'."""
    # Find what class the variable is an instance of
    class_name = find_instance_class(document, var_name)
    if not class_name:
        return None

    # Find the class and its parameters
    classes = find_parameterized_classes(document)
    for cls in classes:
        if cls["name"] == class_name:
            for param in cls["params"]:
                if param["name"] == attr_name:
                    return param
    return None


def build_hover_content(param_info: dict) -> str:
    """Build markdown hover content for a parameter."""
    name = param_info["name"]
    param_type = param_info["param_type"]
    args = param_info["args"]

    # Get Python type and description
    py_type, description = PARAM_TYPE_INFO.get(param_type, ("Any", "Parameter"))

    # Build markdown
    lines = [
        f"### `{name}: {py_type}`",
        "",
        f"**Type:** `{param_type}`",
        "",
        f"_{description}_",
        "",
    ]

    # Add parsed attributes
    if args:
        lines.append("**Attributes:**")
        for key, value in args.items():
            lines.append(f"- `{key}`: {value}")

    return "\n".join(lines)


@server.feature(lsp.TEXT_DOCUMENT_HOVER)
def hover(params: lsp.HoverParams) -> lsp.Hover | None:
    """Provide hover information for param declarations and attribute access."""
    document = server.workspace.get_text_document(params.text_document.uri)

    # First, try to find a param declaration at this position
    param_info = find_param_at_position(document, params.position)

    # If not a declaration, check for attribute access (e.g., person.name)
    if not param_info:
        lines = document.source.split("\n")
        if params.position.line < len(lines):
            line = lines[params.position.line]
            # Find all attribute accesses in this line
            for match in ATTR_ACCESS_PATTERN.finditer(line):
                # Check if cursor is within this match
                if match.start() <= params.position.character <= match.end():
                    var_name, attr_name = match.groups()
                    param_info = find_param_for_attribute(document, var_name, attr_name)
                    break

    if not param_info:
        return None

    content = build_hover_content(param_info)

    return lsp.Hover(
        contents=lsp.MarkupContent(
            kind=lsp.MarkupKind.Markdown,
            value=content,
        )
    )


@server.feature(lsp.TEXT_DOCUMENT_COMPLETION)
def completion(params: lsp.CompletionParams) -> lsp.CompletionList | None:
    """Provide completion for param types and parameter names."""
    document = server.workspace.get_text_document(params.text_document.uri)
    lines = document.source.split("\n")

    if params.position.line >= len(lines):
        return None

    line = lines[params.position.line]
    char_pos = params.position.character
    text_before_cursor = line[:char_pos]

    items = []

    # Case 1: Completing param types (after "param.")
    if text_before_cursor.rstrip().endswith("param."):
        for param_type, (py_type, doc) in PARAM_TYPE_INFO.items():
            type_name = param_type.replace("param.", "")
            items.append(
                lsp.CompletionItem(
                    label=type_name,
                    kind=lsp.CompletionItemKind.Class,
                    detail=f"→ {py_type}",
                    documentation=lsp.MarkupContent(
                        kind=lsp.MarkupKind.Markdown,
                        value=f"**{param_type}**\n\n{doc}\n\nPython type: `{py_type}`",
                    ),
                    insert_text=f"{type_name}($0)",
                    insert_text_format=lsp.InsertTextFormat.Snippet,
                )
            )
        return lsp.CompletionList(is_incomplete=False, items=items)

    # Case 2: Completing parameter kwargs (inside param.Type(...))
    # Check if we're inside a param declaration
    param_match = re.match(r"^\s*\w+\s*=\s*param\.(\w+)\s*\(", line)
    if param_match and "(" in text_before_cursor and ")" not in text_before_cursor:
        param_type_name = param_match.group(1)

        # Common kwargs for all param types
        common_kwargs = [
            ("default", "Default value for this parameter"),
            ("doc", "Documentation string for this parameter"),
            ("constant", "If True, value cannot be changed after instantiation"),
            ("readonly", "If True, value cannot be set by user"),
            ("allow_None", "If True, None is an allowed value"),
            ("label", "Human-readable label for this parameter"),
            ("precedence", "Numeric precedence for UI ordering"),
            ("instantiate", "If True, default value is deep-copied per instance"),
            ("per_instance", "If True, separate Parameter object per instance"),
        ]

        # Type-specific kwargs
        type_specific = {
            "Integer": [("bounds", "Tuple of (min, max) bounds")],
            "Number": [
                ("bounds", "Tuple of (min, max) bounds"),
                ("softbounds", "Tuple of (min, max) soft bounds for UI"),
                ("step", "Step size for UI sliders"),
            ],
            "String": [("regex", "Regular expression pattern to validate against")],
            "Selector": [("objects", "List or dict of valid objects to select from")],
            "ListSelector": [("objects", "List or dict of valid objects to select from")],
            "ClassSelector": [
                ("class_", "Class or tuple of classes to accept"),
                ("is_instance", "If True, require instance; if False, require subclass"),
            ],
            "List": [
                ("item_type", "Type constraint for list items"),
                ("bounds", "Tuple of (min_length, max_length)"),
            ],
            "Path": [("check_exists", "If True, path must exist"), ("search_paths", "List of paths to search")],
            "Range": [("bounds", "Tuple of (min, max) bounds"), ("softbounds", "Tuple of soft bounds")],
        }

        all_kwargs = common_kwargs + type_specific.get(param_type_name, [])

        for kwarg, doc in all_kwargs:
            items.append(
                lsp.CompletionItem(
                    label=kwarg,
                    kind=lsp.CompletionItemKind.Property,
                    detail="param kwarg",
                    documentation=doc,
                    insert_text=f"{kwarg}=$0",
                    insert_text_format=lsp.InsertTextFormat.Snippet,
                )
            )

        return lsp.CompletionList(is_incomplete=False, items=items)

    # Case 3: Completing class instantiation parameters
    # Look for patterns like "MyClass(" where MyClass is a Parameterized class
    class_instantiation = re.search(r"(\w+)\s*\($", text_before_cursor)
    if class_instantiation:
        class_name = class_instantiation.group(1)
        # Find the class in this document
        classes = find_parameterized_classes(document)
        for cls in classes:
            if cls["name"] == class_name:
                for p in cls["params"]:
                    py_type, _ = PARAM_TYPE_INFO.get(p["param_type"], ("Any", ""))
                    items.append(
                        lsp.CompletionItem(
                            label=p["name"],
                            kind=lsp.CompletionItemKind.Field,
                            detail=f": {py_type}",
                            documentation=f"Parameter `{p['name']}` of type `{p['param_type']}`",
                            insert_text=f"{p['name']}=$0",
                            insert_text_format=lsp.InsertTextFormat.Snippet,
                        )
                    )
                return lsp.CompletionList(is_incomplete=False, items=items)

    return None


@server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: lsp.DidOpenTextDocumentParams):
    """Handle document open - publish diagnostics."""
    document = server.workspace.get_text_document(params.text_document.uri)
    diagnostics = analyze_document(document)
    server.publish_diagnostics(params.text_document.uri, diagnostics)


@server.feature(lsp.WORKSPACE_DID_CHANGE_WATCHED_FILES)
def did_change_watched_files(params: lsp.DidChangeWatchedFilesParams):
    """Handle file system changes - silently ignore for now."""
    pass


@server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def did_change(params: lsp.DidChangeTextDocumentParams):
    """Handle document change - update diagnostics."""
    document = server.workspace.get_text_document(params.text_document.uri)
    diagnostics = analyze_document(document)
    server.publish_diagnostics(params.text_document.uri, diagnostics)


def analyze_document(document: TextDocument) -> list[lsp.Diagnostic]:
    """Analyze document for param-related issues."""
    diagnostics = []
    lines = document.source.split("\n")

    for line_num, line in enumerate(lines):
        match = PARAM_PATTERN.match(line)
        if not match:
            continue

        name, full_type, type_name, args = match.groups()

        # Check if param type is known
        if full_type not in PARAM_TYPE_INFO:
            diagnostics.append(
                lsp.Diagnostic(
                    range=lsp.Range(
                        start=lsp.Position(line=line_num, character=match.start(2)),
                        end=lsp.Position(line=line_num, character=match.end(2)),
                    ),
                    message=f"Unknown param type: {full_type}",
                    severity=lsp.DiagnosticSeverity.Information,
                    source="param-lsp",
                )
            )

        # Check for missing 'objects' in Selector types
        parsed_args = parse_param_args(args)
        if type_name in ("Selector", "ListSelector") and "objects" not in parsed_args:
            diagnostics.append(
                lsp.Diagnostic(
                    range=lsp.Range(
                        start=lsp.Position(line=line_num, character=match.start(3)),
                        end=lsp.Position(line=line_num, character=match.end(3)),
                    ),
                    message=f"{type_name} should specify 'objects' parameter",
                    severity=lsp.DiagnosticSeverity.Warning,
                    source="param-lsp",
                )
            )

        # Check for bounds on numeric types
        if type_name in ("Integer", "Number") and "bounds" not in parsed_args:
            diagnostics.append(
                lsp.Diagnostic(
                    range=lsp.Range(
                        start=lsp.Position(line=line_num, character=match.start(3)),
                        end=lsp.Position(line=line_num, character=match.end(3)),
                    ),
                    message=f"Consider adding 'bounds' to {type_name} for better validation",
                    severity=lsp.DiagnosticSeverity.Hint,
                    source="param-lsp",
                )
            )

    return diagnostics


if __name__ == "__main__":
    print("Starting param-lsp server on stdio...")
    print("Features: hover, completion, diagnostics")
    server.start_io()
