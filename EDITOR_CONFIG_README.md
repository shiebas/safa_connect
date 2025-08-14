# Editor Configuration for SAFA Connect Project

## Overview

This project uses EditorConfig to maintain consistent coding styles across different editors and IDEs. EditorConfig helps ensure that all contributors follow the same coding standards, regardless of the editor they use.

## What is EditorConfig?

EditorConfig is a file format and collection of text editor plugins that enable editors to maintain consistent coding styles between different editors and IDEs. The EditorConfig project consists of a file format for defining coding styles and a collection of text editor plugins that enable editors to read the file format and adhere to defined styles.

## How it Works

The `.editorconfig` file at the root of the project defines the coding style rules. When you open a file in an editor that supports EditorConfig, it will apply these rules automatically.

## Key Settings in Our Configuration

- **All files**: UTF-8 encoding, LF line endings, 4-space indentation, and trimming of trailing whitespace
- **HTML/CSS/JS/Django templates**: 4-space indentation
- **Python files**: 4-space indentation, max line length of 119 characters (PEP 8 compliant)
- **YAML/JSON files**: 2-space indentation
- **Windows batch files**: CRLF line endings

## Editor Support

Most modern editors support EditorConfig either natively or through plugins:

### Native Support
- Visual Studio Code
- IntelliJ IDEA
- PyCharm
- WebStorm
- PhpStorm
- Rider
- Android Studio

### Plugin Required
- Sublime Text: [EditorConfig for Sublime Text](https://github.com/sindresorhus/editorconfig-sublime)
- Vim: [editorconfig-vim](https://github.com/editorconfig/editorconfig-vim)
- Emacs: [editorconfig-emacs](https://github.com/editorconfig/editorconfig-emacs)
- Atom: [editorconfig](https://github.com/sindresorhus/atom-editorconfig)
- Notepad++: [EditorConfig Notepad++ Plugin](https://github.com/editorconfig/editorconfig-notepad-plus-plus)

## Installation Instructions

### Visual Studio Code
EditorConfig support is built-in, no extension needed.

### PyCharm/IntelliJ
EditorConfig support is built-in, no plugin needed.

### Sublime Text
1. Install Package Control if you haven't already
2. Open Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
3. Select "Package Control: Install Package"
4. Search for "EditorConfig" and install it

### Vim
Add to your `.vimrc`:
```
Plugin 'editorconfig/editorconfig-vim'
```

### Notepad++
1. Open Plugin Manager
2. Search for "EditorConfig" and install it

## Troubleshooting

If your editor is not respecting the EditorConfig settings:

1. Make sure your editor has EditorConfig support installed
2. Check if there are any editor-specific settings that might be overriding the EditorConfig settings
3. Restart your editor after installing EditorConfig support

## Why This Matters

Using EditorConfig helps prevent issues with:
- Mixed indentation (tabs vs spaces)
- Inconsistent line endings (CRLF vs LF)
- Trailing whitespace
- Character encoding problems

These inconsistencies can cause problems in version control systems, make code reviews more difficult, and lead to rendering issues in different environments.
