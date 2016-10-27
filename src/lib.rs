extern crate libc;

use libc::{size_t, uint32_t};
use std::slice;
use std::mem;

use std::thread;
use std::sync::{Arc, Mutex};

#[repr(C)]
/// Struct to pass Vec properties over ffi
pub struct VectorU32 {
    data: *const uint32_t,
    len: size_t,
    cap: size_t,
}

impl VectorU32 {
    fn from_vec(vec: &Vec<u32>) -> VectorU32 {
        VectorU32 {data: vec.as_ptr(), len: vec.len(), cap: vec.capacity()}
    }
}

#[no_mangle]
pub extern fn fib_slow(n: u32) -> u32 {
    if n == 0 || n == 1 { n }
    else { fib_slow(n-1) + fib_slow(n-2) }
}

//pub fn fib_fast(n: u32) -> u32 {
//    let mut a = 1;
//    let mut b = 1;
//    let mut h;
//    for _ in 0..n {
//        h = a;
//        a = b;
//        b = h + b;
//    }
//    a
//}

/// Calculate fib. of list in separate threads
pub fn fib_many(many: &[u32]) -> Vec<u32> {
    let results = Arc::new(Mutex::new(Vec::with_capacity(many.len())));
    let handles: Vec<_> = many.iter().cloned().map(|n| {
        let results = results.clone();
        thread::spawn(move || {
            let res = fib_slow(n);
            let mut results = results.lock().unwrap();
            results.push(res);
        })
    }).collect();
    for h in handles {
        h.join().ok().expect("could not join");
    }
    let results = results.lock().unwrap().iter().cloned().collect::<Vec<_>>();
    results
}

#[no_mangle]
/// Calculate fib. sequentially from a list, return a new list
pub extern fn fib_seq_results(data: *const uint32_t, length: size_t) -> VectorU32 {
    let nums = unsafe { slice::from_raw_parts(data, length as usize) };
    let results = nums.iter().map(|&n| fib_slow(n)).collect::<Vec<_>>();
    let vec = VectorU32::from_vec(&results);
    println!("[from-rust] create: {:?}", results.as_ptr());
    println!("[from-rust] create: {:?}", results);
    mem::forget(results);
    vec
}

#[no_mangle]
/// Calculate fib. with threading from a list, return the count
pub extern fn fib_threaded(data: *const uint32_t, length: size_t) -> uint32_t {
    let nums = unsafe { slice::from_raw_parts(data, length as usize) };
    let results = fib_many(nums);
    results.len() as u32
}

#[no_mangle]
/// Calculate fib. with threading from a list, return a new list
pub extern fn fib_threaded_results(data: *const uint32_t, length: size_t) -> VectorU32 {
    let nums = unsafe { slice::from_raw_parts(data, length as usize) };
    let results = fib_many(nums);
    let vec = VectorU32::from_vec(&results);
    println!("[from-rust] create: {:?}", results.as_ptr());
    println!("[from-rust] create: {:?}", results);
    mem::forget(results);
    vec
}

#[no_mangle]
/// Drop a rust-made vec
pub extern fn drop_vec(data_ptr: *mut uint32_t, len: size_t, cap: size_t) {
    assert!(!data_ptr.is_null());
    let vec = unsafe { Vec::from_raw_parts(data_ptr, len as usize, cap as usize) };
    println!("[from-rust] drop:   {:?}", vec.as_ptr());
    println!("[from-rust] drop:   {:?}", vec);
    // mem::drop(vec);  // can also explicitly drop
}
