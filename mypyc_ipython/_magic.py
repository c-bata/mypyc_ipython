"""Magic command interface for interactive work with Mypyc

To enable the magics below, execute ``%load_ext mypyc_ipython``.
"""
import io
import os
import sys
import time
import distutils.log
import hashlib
from distutils.core import Distribution
from distutils.command.build_ext import build_ext
import importlib.machinery

from mypyc.build import get_extension, mypycify
from mypy.version import __version__ as mypy_version

from IPython.core import magic_arguments
from IPython.core.magic import Magics, magics_class, cell_magic

try:
    from IPython.paths import get_ipython_cache_dir
except ImportError:
    # older IPython version
    from IPython.utils.path import get_ipython_cache_dir

IO_ENCODING = sys.getfilesystemencoding()
Extension = get_extension()


@magics_class
class MypycMagics(Magics):
    def __init__(self, shell):
        super(MypycMagics, self).__init__(shell)
        self._reloads = {}
        self._code_cache = {}

    def _import_all(self, module):
        mdict = module.__dict__
        if "__all__" in mdict:
            keys = mdict["__all__"]
        else:
            keys = [k for k in mdict if not k.startswith("_")]

        for k in keys:
            try:
                self.shell.push({k: mdict[k]})
            except KeyError:
                msg = "'module' object has no attribute '%s'" % k
                raise AttributeError(msg)

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force the compilation of a new module, even if the source has been "
        "previously compiled.",
    )
    @magic_arguments.argument(
        "--verbose",
        dest="quiet",
        action="store_false",
        default=True,
        help=(
            "Print debug information like generated .c/.cpp file location "
            "and exact gcc/g++ command invoked."
        ),
    )
    @cell_magic
    def mypyc(self, line, cell):
        """Compile and import everything from a mypyc code cell.

        The contents of the cell are written to a `.py` file in the
        directory `IPYTHONDIR/mypyc` using a filename with the hash of the
        code. This file is then mypycified and compiled. The resulting module
        is imported and all of its symbols are injected into the user's
        namespace.

            %%mypyc
            def mypyc_fib(n: int) -> float:
                i: int
                a: float = 0.0
                b: float = 1.0
                for i in range(n):
                    a, b = a + b, a
                return a
        """
        args = magic_arguments.parse_argstring(self.mypyc, line)
        code = cell if cell.endswith("\n") else cell + "\n"
        lib_dir = os.path.join(get_ipython_cache_dir(), "mypyc")
        key = (code, line, sys.version_info, sys.executable, mypy_version)

        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)

        if args.force:
            # Force a new module name by adding the current time to the
            # key which is hashed to determine the module name.
            key += (time.time(),)

        module_name = (
            "_mypyc_magic_" + hashlib.sha1(str(key).encode("utf-8")).hexdigest()
        )
        module_path = os.path.join(lib_dir, module_name + self.so_ext)
        need_mypycify = not os.path.isfile(module_path)

        extension = None
        if need_mypycify:
            extensions = self._mypycify(
                module_name, code, lib_dir, args, quiet=args.quiet
            )
            if extensions is None:
                # Compilation failed and printed error message
                return None
            assert len(extensions) == 1
            extension = extensions[0]
            self._code_cache[key] = module_name

        try:
            self._build_extension(extension, lib_dir, quiet=args.quiet)
        except distutils.errors.CompileError:
            # Build failed and printed error message
            return None

        loader = importlib.machinery.ExtensionFileLoader(module_name, module_path)
        spec = importlib.machinery.ModuleSpec(
            name=module_name, loader=loader, origin=module_path
        )
        module = importlib._bootstrap._load(spec)
        self._import_all(module)

    def _mypycify(self, module_name, code, lib_dir, args, quiet=True):
        py_file = os.path.join(lib_dir, module_name + ".py")
        with io.open(py_file, "w", encoding="utf-8") as f:
            f.write(code)
        return mypycify([py_file], verbose=not quiet, opt_level="3")

    def _build_extension(self, extension, lib_dir, temp_dir=None, quiet=True):
        build_extension = self._get_build_extension(
            extension, lib_dir=lib_dir, temp_dir=temp_dir
        )
        old_threshold = None
        try:
            if not quiet:
                old_threshold = distutils.log.set_threshold(distutils.log.DEBUG)
            build_extension.run()
        finally:
            if not quiet and old_threshold is not None:
                distutils.log.set_threshold(old_threshold)

    @property
    def so_ext(self):
        """The extension suffix for compiled modules."""
        try:
            return self._so_ext
        except AttributeError:
            self._so_ext = self._get_build_extension().get_ext_filename("")
            return self._so_ext

    def _clear_distutils_mkpath_cache(self):
        """clear distutils mkpath cache

        prevents distutils from skipping re-creation of dirs that have been removed
        """
        try:
            from distutils.dir_util import _path_created
        except ImportError:
            pass
        else:
            _path_created.clear()

    def _get_build_extension(
        self, extension=None, lib_dir=None, temp_dir=None, _build_ext=build_ext
    ):
        self._clear_distutils_mkpath_cache()
        dist = Distribution()
        config_files = dist.find_config_files()
        try:
            config_files.remove("setup.cfg")
        except ValueError:
            pass
        dist.parse_config_files(config_files)

        if not temp_dir:
            temp_dir = lib_dir

        build_extension = _build_ext(dist)
        build_extension.finalize_options()
        if temp_dir:
            build_extension.build_temp = temp_dir
        if lib_dir:
            build_extension.build_lib = lib_dir
        if extension is not None:
            build_extension.extensions = [extension]
        return build_extension
