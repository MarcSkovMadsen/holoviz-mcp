const path = require('path');
const { LanguageClient, TransportKind } = require('vscode-languageclient/node');

let client;

function activate(context) {
    // Path to the Python LSP server - use absolute path
    const serverPath = '/home/jovyan/repos/private/holoviz-mcp/examples/param-lsp/param_lsp.py';

    console.log('Starting Param LSP server:', serverPath);

    const serverOptions = {
        command: 'python',
        args: [serverPath],
        transport: TransportKind.stdio
    };

    const clientOptions = {
        // Register for Python files
        documentSelector: [{ scheme: 'file', language: 'python' }],
        synchronize: {
            // Watch for .py file changes
            fileEvents: require('vscode').workspace.createFileSystemWatcher('**/*.py')
        }
    };

    // Create and start the language client
    client = new LanguageClient(
        'param-lsp',
        'Param LSP',
        serverOptions,
        clientOptions
    );

    client.start();
    console.log('Param LSP client started');
}

function deactivate() {
    if (!client) {
        return undefined;
    }
    return client.stop();
}

module.exports = { activate, deactivate };
