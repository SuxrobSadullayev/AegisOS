# Runtime Loader

## Purpose

The Context Loader reads static Markdown files from `core/`, `modules/`, and `knowledge/` layers.

## Scripts

- `loader.sh` — POSIX-compliant shell script to read and stream core context or target module files.

## Usage

```bash
# Load all Layer 0 Core files
./runtime/loaders/loader.sh core

# Load specific file
./runtime/loaders/loader.sh file core/kernel/constitution.md
```
