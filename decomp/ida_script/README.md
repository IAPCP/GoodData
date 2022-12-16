# IDA Decompile Dump
## Usage
1. add idat64 or ida64.exe into your `PATH`
``` bash
    idat64 -A -S"{idascript_path} {arg1}" -L{log_path} {target_binary_path}
```

## Tips
If you use VSCode as your code editor, you can use the following settings to make the source code more readable (with ida libraries highlighted).
1. install VSCode plugin `Python` and `Pylance`
2. open settings and find `python.analysis.extraPaths`
3. add your ida libraries' path into it

## Requirement
IDA version >= 7.4