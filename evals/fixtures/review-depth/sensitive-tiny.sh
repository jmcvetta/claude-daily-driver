#!/usr/bin/env bash
# Rewrites the release workflow under .github/workflows/.
# shellcheck source=./lib.sh
source "$(dirname "$0")/lib.sh"
# shellcheck source=./_common_base.sh
source "$(dirname "$0")/_common_base.sh"

fixture_init
fixture_write_base_tree
fixture_publish_base
fixture_branch ci/publish-on-tag

cat >.github/workflows/release.yml <<'EOF'
name: Release

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

permissions:
  contents: write
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: true
      - run: python -m build
      - env:
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: python -m twine upload dist/*
EOF

fixture_publish_topic "ci: publish on tag, and on demand"
