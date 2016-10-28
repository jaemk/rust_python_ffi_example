### Rust <-> Python ffi example

For future reference...
----

Some examples showing how to pass a primitive u32 and a more complicated
rust-Vec <-> python-list over ffi using ctypes.


    cargo build --release
    ./src/fib.py --help
    # ** Rust<->Python fib test
    #    Optional args:
    #            --fib <n>  # nth fibonacci digit to calculate, default: 30
    #            --rep <n>  # number of times to repeat the calculation, default: 15

