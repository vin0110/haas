# Testing

To perform all tests from root directory
```shell
python -m unittest discover tests
```
The last parameter is the _tests_ directory.
If executing above command in a different directory from the root project
directory, use a different directory.
E.g., use
```shell
python -m unittest discover .
```
from the _tests_ directory itself.

Add `-v` to get verbose mode, i.e.,
```shell
python -m unittest discover tests -v
```

To execute a specific test file use `-p PATTERN`, e.g.,
```shell
python -m unittest discover tests -p test_stack_list.py
```
