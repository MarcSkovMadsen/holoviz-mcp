#!/bin/bash

# For writing commands that will be executed after the container is created
set -e

sudo chown vscode .pixi
pixi install --all
