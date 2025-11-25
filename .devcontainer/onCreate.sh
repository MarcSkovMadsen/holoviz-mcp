#!/bin/bash

# For writing commands that will be executed after the container is created
set -e

pixi install --all
if [ -d .pixi ]; then
    sudo chown -R vscode .pixi
fi
