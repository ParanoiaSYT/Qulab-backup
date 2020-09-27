import lzma
import pickle
import struct
from typing import Any, Callable, TypeVar

import numpy as np
from qulab import umsgpack

__index = 0
__pack_handlers = {}
__unpack_handlers = {}

cls = TypeVar('cls')


def register(cls: type,
             encode: Callable[[cls], bytes] = pickle.dumps,
             decode: Callable[[bytes], cls] = pickle.loads) -> None:
    """
    Register a serializable type

    Args:
        cls: type
        encode: Callable
            translate an object of type `cls` into `bytes`
            default: pickle.dumps
        decode: Callable
            translate `bytes` to an object of type `cls`
            default: pickle.loads
    """
    global __index
    __index += 1
    t = __index
    __pack_handlers[cls] = lambda obj: umsgpack.Ext(t, encode(obj))
    __unpack_handlers[t] = lambda ext: decode(ext.data)


def pack(obj: Any) -> bytes:
    """
    Serialize
    """
    return umsgpack.packb(obj, ext_handlers=__pack_handlers)


def unpack(buff: bytes) -> Any:
    """
    Unserialize
    """
    return umsgpack.unpackb(buff, ext_handlers=__unpack_handlers)


def packz(obj: Any) -> bytes:
    """
    Serialize and compress.
    """
    return lzma.compress(pack(obj), format=lzma.FORMAT_XZ)


def unpackz(buff: bytes) -> Any:
    """
    Decompress and unserialize.
    """
    return unpack(lzma.decompress(buff, format=lzma.FORMAT_XZ))


register(np.ndarray)


def encode_excepion(e: Exception) -> bytes:
    e.__traceback__ = None
    return pickle.dumps(e)


register(Exception, encode_excepion)
