extern crate rust_python_ffi_example;

use std::env;

use rust_python_ffi_example::*;

pub fn main() {
    let args = env::args().map(|s| s.parse::<u32>())
                          .filter(|res| res.is_ok())
                          .map(|res| res.unwrap())
                          .collect::<Vec<_>>();
    println!("{:?}", fib_many(args.as_slice()));
    //fib_threaded_results(args.as_ptr(), args.len());  // also works
}
