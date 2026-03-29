---
name: dir
description: Directory listing and exploration tool. Use when the user wants to (1) list files and folders in a directory, (2) show directory tree structure, (3) filter files by pattern or extension, (4) get file details like size/type/date, or (5) explore project structure. Triggers on commands like "dir", "ls", "list files", "show directory", "tree", "what's in this folder".
author: charlie
---

# Directory Listing

List and explore directory contents with filtering and tree views.

## Basic Listing

List files in a directory:

```
Glob pattern: "path/to/dir/*"
```

List specific file types:

```
Glob pattern: "src/**/*.ts"     # All .ts files recursively
Glob pattern: "*.json"           # JSON files in current dir
```

## Recursive Tree View

For a formatted tree structure, use Bash:

```bash
# Simple tree (if tree command available)
tree /path/to/dir -L 3

# Without tree command
find /path/to/dir -type f | head -50
```

## File Details

Get detailed file info with Bash:

```bash
# List with details (size, date, permissions)
ls -la /path/to/dir

# Human-readable sizes
ls -lah /path/to/dir

# Sort by size
ls -laS /path/to/dir

# Sort by time
ls -lat /path/to/dir
```

## Common Patterns

| Task | Approach |
|------|----------|
| List all files | `Glob pattern: "**/*"` |
| Find by extension | `Glob pattern: "**/*.py"` |
| Find directories | `Glob pattern: "**/"` then filter |
| File count | Bash: `find . -type f \| wc -l` |
| Directory size | Bash: `du -sh /path` |
| Recent files | Bash: `ls -lt \| head -10` |
| Large files | Bash: `du -ah \| sort -rh \| head -10` |

## Notes

- Use Glob for pattern matching (faster, built-in)
- Use Bash for detailed listings and sorting
- Default to relative paths from current working directory
- For Windows paths, use forward slashes: `C:/Users/...`
