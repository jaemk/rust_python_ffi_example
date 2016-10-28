#!/usr/bin/python3

import os
import sys
import time
import ctypes

from collections import namedtuple


class FFIVectorU32(ctypes.Structure):
    """ Object for passing rust Vec properties over ffi """
    _fields_ = [('data', ctypes.c_uint32),
                ('len', ctypes.c_size_t),
                ('cap', ctypes.c_size_t)]


def vector_u32_to_list(answer, _ffi_func, _ffi_args):
    """
    Checks/cleans the output of ffi-funcs. Intended for
    funcs with an FFIVectoryU32 restype.
    Enabled by setting:
        `lib.ffi-func.errcheck = vector_u32_to_list`

    :param answer: FFIVectorU32 object
    :param _ffi_func: foreign func object
    :param _ffi_args: tuple or args passed to the _ffi_func
    """
    Vec = namedtuple('Vec', ['ptr', 'data', 'len', 'cap'])
    # need to save the ptr, len, and cap so we can properly ask
    # rust to clean up the Vec that it created by calling:
    # `lib.drop_vec(Vec.ptr, Vec.len, Vec.cap)`
    data_ptr = ctypes.cast(answer.data, ctypes.POINTER(ctypes.c_uint32))
    data = [data_ptr[i] for i in range(answer.len)]
    return Vec(data_ptr, data, answer.len, answer.cap)


# Load our dylib/shared-object file
src_dir = os.path.dirname(os.path.abspath(__file__))
so_libname = 'librust_python_ffi_example.so'
so_location = os.path.join('.', src_dir, '..', 'target', 'release', so_libname)
lib = ctypes.cdll.LoadLibrary(so_location)

# Simple ffi passing and receiving u32's - don't need to specify restype
# or manually cleanup any memory
lib.fib_slow.argtypes = (ctypes.c_uint32, )

# More complex... Here we're going to pass a list to rust which will read it
# as an immutable slice and then create and return a new (rust) Vec as an
# FFIVectorU32 that has the details required to read the values into a python list.
# Since rust created the Vec it also needs to deallocate it, by passing the Vec
# ptr, size, and cap back to rust with lib.drop_vec below. Note, the Vec.data
# that was copied into a python list is a normal python list and is still available.
lib.fib_seq_results.argtypes = (ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t)
lib.fib_seq_results.restype = FFIVectorU32
lib.fib_seq_results.errcheck = vector_u32_to_list

# Less complex... Here we're giving a list to rust which will read it, calculate
# fib numbers and then return the number of fibs calculated.
lib.fib_threaded.argtypes = (ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t)

# Same as lib.fib_seq_results
lib.fib_threaded_results.argtypes = (ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t)
lib.fib_threaded_results.restype  = FFIVectorU32
lib.fib_threaded_results.errcheck = vector_u32_to_list

# Passes Vec info back to rust so it can reclaim the memory it allocated
lib.drop_vec.argtypes = (ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t, ctypes.c_size_t)


def fib_slow(n):
    if n == 0 or n == 1:
        return n
    else:
        return fib_slow(n-1) + fib_slow(n-2)


#def fib_fast(n):
#    a, b = 1, 1
#    for i in range(n-1):
#        a, b = b, a+b
#    return a


def into_c_uint32(seq):
    return (ctypes.c_uint32 * len(seq))(*seq)


def main(args):
    _help = """** Rust<->Python fib test
    Optional args:
        --fib <n>  # nth fibonacci digit to calculate, default: 30
        --rep <n>  # number of times to repeat the calculation, default: 15
    """
    ARGS = {'--fib': 30, '--rep': 15}
    if args:
        if len(args) % 2 != 0 or len(args) > 4:
            print(_help)
            return
        for i in range(0, len(args), 2):
            opt, n = args[i:i+2]
            try:
                n = int(n)
                if opt not in ARGS:
                    raise ValueError
            except ValueError:
                print(_help)
                return
            ARGS[opt] = n

    nums = [ARGS['--fib'] for _ in range(ARGS['--rep'])]
    nums.reverse()
    c_nums = into_c_uint32(nums)

    print('** Doing a slow recursive fib. on:\n{}\n'.format(nums))

    print('** python fibbing sequentially')
    start = time.time()
    fibs = [fib_slow(n) for n in nums]
    print('>> done in {}\n'.format(time.time() - start))

    print('** rust fibbing sequentially, inside a python list-comp')
    start = time.time()
    fibs = [lib.fib_slow(n) for n in nums]
    print('>> done in {}\n'. format(time.time() - start))

    print('** rust fibbing sequentially [from a list], returning a new list')
    start = time.time()
    ans = lib.fib_seq_results(c_nums, len(nums))
    lib.drop_vec(ans.ptr, ans.len, ans.cap)
    print('>> done in {}\n'.format(time.time() - start))

    print('** rust fibbing with threads [from a list], returning total count')
    start = time.time()
    lib.fib_threaded(c_nums, len(nums))
    print('>> done in {}\n'.format(time.time() - start))

    print('** rust fibbing with threads [from a list], returning a new list')
    start = time.time()
    ans  = lib.fib_threaded_results(c_nums, len(nums))
    lib.drop_vec(ans.ptr, ans.len, ans.cap)
    print('>> done in {}\n'.format(time.time() - start))


    print('** Test memory alloc/free')
    for i in range(2):
        print(' <> {}.)'.format(i+1))
        ans = lib.fib_threaded_results(c_nums, len(nums))
        lib.drop_vec(ans.ptr, ans.len, ans.cap)


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)

