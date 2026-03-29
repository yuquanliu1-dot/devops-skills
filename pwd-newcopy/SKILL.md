---
name: pwd-newcopy
description: Print the current working directory and count files. Use when you need to know the current directory path or count the number of files in a directory.
version: 1.1.0
author: CharlieLYQY
tags: [utility, filesystem, navigation, counting]
---

# pwd - Print Working Directory & File Counter

Print the absolute path of the current working directory and optionally count files in directories.

## Usage

```
/pwd              # Print current working directory
/pwd --count      # Count files in current directory
/pwd --count -r   # Count files recursively (including subdirectories)
```

## Description

This skill provides two main functions:

1. **Print Working Directory**: Display the full absolute path of the current working directory
2. **File Counting**: Count the number of files in a directory

## Examples

### Print Current Directory

```
/pwd
```

Output example:
```
Current working directory: /home/user/projects/myapp
```

### Count Files in Current Directory

```
/pwd --count
```

Output example:
```
Current working directory: /home/user/projects/myapp
Files in current directory: 15
```

### Count Files Recursively

```
/pwd --count -r
```

Output example:
```
Current working directory: /home/user/projects/myapp
Total files (recursive): 127
Directories scanned: 12
```

## Use Cases

- Verify your current location in the filesystem
- Copy the current path for use in other commands
- Debug path-related issues in scripts or commands
- Confirm directory changes after `cd` operations
- Quickly count files in a project directory
- Get file statistics before performing bulk operations

## How It Works

When you run `/pwd`, Claude will:

1. Execute a command to retrieve the current working directory
2. Display the absolute path to you

When you run `/pwd --count`, Claude will:

1. Get the current working directory
2. Count all files (not directories) in the current location
3. Display both the path and file count

When you run `/pwd --count -r`, Claude will:

1. Get the current working directory
2. Recursively count all files in all subdirectories
3. Display the path, total file count, and directories scanned

## Notes

- On Windows, the path will use backslashes (e.g., `C:\Users\username\project`)
- On Unix/Linux/macOS, the path will use forward slashes (e.g., `/home/username/project`)
- The path returned is always an absolute path, not a relative one
- File counting excludes directories (only counts actual files)
- Recursive counting includes hidden files (files starting with `.` on Unix/Linux)

## Related Commands

- `cd` - Change directory
- `ls` - List directory contents
- `find` - Search for files
