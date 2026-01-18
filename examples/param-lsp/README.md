# Minimal LSP Server for param

A minimal Language Server Protocol (LSP) implementation that provides IDE features for `param.Parameterized` classes.

## Current Status

This is a **proof-of-concept** LSP server demonstrating what's possible for param tooling. It uses simple regex-based parsing (not a full Python AST parser) and only analyzes the current file.

### Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Hover (declarations)** | ✅ | Hover over `param.Integer(...)` to see type info |
| **Hover (attribute access)** | ✅ | Hover over `person.name` to see param info (same file only) |
| **Completion (param types)** | ✅ | Type `param.` to see all param types |
| **Completion (kwargs)** | ✅ | Inside `param.Number(...)`, get suggestions for `bounds`, `doc`, etc. |
| **Completion (instantiation)** | ✅ | Type `Person(` to see parameter names |
| **Diagnostics** | ✅ | Warnings for unknown types, missing `objects` in Selectors |
| **Cross-file resolution** | ❌ | Only works within the current file |
| **Type checking** | ❌ | Does not replace Pylance/Pyright |

### Limitations

- **Regex-based parsing**: May fail on complex multi-line declarations
- **Same-file only**: Cannot resolve classes or variables from imports
- **No inheritance tracking**: Doesn't resolve inherited parameters from parent classes in other files
- **Runs alongside Pylance**: Pylance may still show type errors (see [Pylance Coexistence](#pylance-coexistence))

## Installation

### Prerequisites

```bash
pip install pygls lsprotocol param
```

### Quick Test

Run the tests to verify the server works:

```bash
cd examples/param-lsp
python test_param_lsp.py
```

Expected output:
```
✓ test_parse_param_args_with_kwargs
✓ test_parse_param_args_with_positional
...
PASSED: All 11 tests passed!
```

## Building the VS Code Extension

The `vscode-client/` folder contains a minimal VS Code extension that launches the LSP server.

### Build Steps

```bash
cd examples/param-lsp/vscode-client

# Install dependencies
npm install

# Package as VSIX
npx vsce package --allow-missing-repository -o param-lsp.vsix
```

This creates `param-lsp.vsix` (~32 MB).

> **Note**: The extension uses an absolute path to `param_lsp.py`. If you move the files, update the path in `extension.js`.

## Installing the Extension

### VS Code (Desktop)

```bash
# Install
code --install-extension examples/param-lsp/vscode-client/param-lsp.vsix

# Or for development (hot reload)
code --extensionDevelopmentPath=/full/path/to/examples/param-lsp/vscode-client
```

### code-server (Web)

```bash
# Install
code-server --install-extension examples/param-lsp/vscode-client/param-lsp.vsix

# Force reinstall (after updates)
code-server --install-extension examples/param-lsp/vscode-client/param-lsp.vsix --force
```

After installation, **reload the window**:
- Press `Ctrl+Shift+P`
- Type "Reload Window"
- Press Enter

### Verify Installation

1. Open a Python file with `param.Parameterized` classes
2. Open the Output panel: `Ctrl+Shift+U` (or View → Output)
3. Select "Param LSP" from the dropdown
4. You should see: `Starting Param LSP server...`

## Uninstalling the Extension

### VS Code (Desktop)

```bash
code --uninstall-extension undefined_publisher.param-lsp-client
```

### code-server (Web)

```bash
code-server --uninstall-extension undefined_publisher.param-lsp-client
```

### Via UI

1. Open Extensions panel: `Ctrl+Shift+X`
2. Search for "Param LSP"
3. Click the gear icon → Uninstall

## Usage

Open `example_parameterized.py` and try:

1. **Hover** over `param.Integer` → see type info and kwargs
2. **Hover** over `person.name` → see the parameter's type and metadata
3. **Type** `param.` → see completion for all param types
4. **Inside** `param.Number(`, press `Ctrl+Space` → see kwargs like `bounds`, `doc`
5. **Type** `Person(` → see completion for `name`, `age`, `height`, etc.

## Pylance Coexistence

This LSP runs **alongside** Pylance (VS Code's Python language server). They don't share information:

```
┌─────────────────┐     ┌─────────────────┐
│    Pylance      │     │   param-lsp     │
│ "name unknown"  │     │ "name: str"     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
              Both show in VS Code
```

**Pylance may still show errors** like "Property 'name' not defined" because it doesn't understand param descriptors.

### Workarounds

1. **Add type annotations** (recommended):
   ```python
   name: str = param.String(default="Alice")
   ```

2. **Disable Pylance for specific files**:
   ```json
   // .vscode/settings.json
   {
     "python.analysis.ignore": ["**/my_parameterized_file.py"]
   }
   ```

3. **Create type stubs** (`param.pyi`) - more complex but fully fixes the issue

## Architecture

```
examples/param-lsp/
├── param_lsp.py              # LSP server (Python)
│   ├── PARAM_TYPE_INFO       # Map: param.Type → Python type
│   ├── hover()               # textDocument/hover handler
│   ├── completion()          # textDocument/completion handler
│   └── analyze_document()    # Diagnostics
├── test_param_lsp.py         # Unit tests
├── example_parameterized.py  # Example file to test with
├── README.md                 # This file
└── vscode-client/            # VS Code extension
    ├── package.json          # Extension manifest
    ├── extension.js          # Extension entry point
    └── node_modules/         # Dependencies
```

## Development

### Running the Server Standalone

For debugging, run the server directly:

```bash
python param_lsp.py
```

The server communicates via stdio using JSON-RPC. You can test with:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}
```

### Modifying the Server

1. Edit `param_lsp.py`
2. No need to rebuild the extension - it reads the Python file directly
3. Reload VS Code window to pick up changes

### Adding New Param Types

Edit `PARAM_TYPE_INFO` in `param_lsp.py`:

```python
PARAM_TYPE_INFO = {
    "param.MyNewType": ("my_python_type", "Description of the type"),
    # ...
}
```

## Future Improvements

To make this production-ready:

1. **Use AST parsing** instead of regex for robust detection
2. **Cross-file resolution** via workspace indexing
3. **Runtime introspection** to get actual Parameter metadata
4. **Mypy/Pyright plugin** to provide types to static checkers
5. **Type stubs generation** for param library

## Related Resources

- [pygls](https://pygls.readthedocs.io/) - Python Language Server library
- [param](https://param.holoviz.org/) - Parameter library for Python
- [LSP Specification](https://microsoft.github.io/language-server-protocol/) - Protocol documentation
- [vscode-languageclient](https://github.com/microsoft/vscode-languageserver-node) - VS Code LSP client
