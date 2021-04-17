__version__ = "0.0.2"


def load_ipython_extension(ip):
    """Load the extension in IPython via %load_ext mypyc_ipython."""
    from ._magic import MypycMagics

    ip.register_magics(MypycMagics)
