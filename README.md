# mypyc_ipython

IPython magic command interface for interactive work with [mypyc](https://github.com/python/mypy), a compiler from type-annotated Python to C extensions.

## Installation

Supported Python versions are 3.6 or later.

```console
$ pip install mypyc-ipython
```

## Usage

You can use this library like [``%%cython`` magic command](https://cython.readthedocs.io/en/latest/src/quickstart/build.html#using-the-jupyter-notebook).

1. Execute ``%load_ext mypyc_ipython`` to enable the magic.
2. Write the code in ``%%mypyc`` code cell.

```python
In [1]: %load_ext mypyc_ipython

In [2]: %%mypyc
   ...: def my_fibonacci(n: int) -> int:
   ...:     if n <= 2:
   ...:         return 1
   ...:     else:
   ...:         return my_fibonacci(n-1) + my_fibonacci(n-2)
   ...:

In [3]: my_fibonacci(10)
Out[3]: 55

In [4]: def py_fibonacci(n: int) -> int:
   ...:     if n <= 2:
   ...:         return 1
   ...:     else:
   ...:         return py_fibonacci(n-1) + py_fibonacci(n-2)
   ...:

In [5]: py_fibonacci(10)
Out[5]: 55

In [6]: %load_ext cython

In [7]: %%cython
   ...: cpdef int cy_fibonacci(int n):
   ...:     if n <= 2:
   ...:         return 1
   ...:     else:
   ...:         return cy_fibonacci(n-1) + cy_fibonacci(n-2)
   ...:

In [8]: cy_fibonacci(10)
Out[8]: 55

In [9]: %timeit py_fibonacci(10)
10.3 µs ± 30.2 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)

In [10]: %timeit my_fibonacci(10)
848 ns ± 5.82 ns per loop (mean ± std. dev. of 7 runs, 1000000 loops each)

In [11]: %timeit cy_fibonacci(10)
142 ns ± 1.18 ns per loop (mean ± std. dev. of 7 runs, 10000000 loops each)

In [12]:
```

The contents of the cell are written to a `.py` file in the directory `IPYTHONDIR/mypyc`
using a filename with the hash of the code. This file is then mypycified and compiled.
The resulting module is imported and all of its symbols are injected into the user's namespace.

If you want to disable the cache, you can use ``--force`` option like this:

```python
In [2]: %%mypyc --force
   ...: def my_fibonacci(n: int) -> int:
   ...:     if n <= 2:
   ...:         return 1
   ...:     else:
   ...:         return my_fibonacci(n-1) + my_fibonacci(n-2)
```

## Author

Masashi Shibata ([@c-bata](https://github.com/c-bata))

## License

MIT License
