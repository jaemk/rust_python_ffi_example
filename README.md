### Rust <-> Python ffi example

For future reference...
----

Some examples showing how to pass a primitive u32 and a more complicated
rust-Vec <-> python-list over ffi using ctypes.


    cargo build --release
    ./src/fib.py <n>      # range(n) -- seq. to calculate fib. for
                          # defaults to 15

