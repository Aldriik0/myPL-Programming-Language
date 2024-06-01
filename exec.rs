#[allow(unused_imports)]
use std::io;
#[allow(unused_imports)]
use std::ptr::null;

#[allow(warnings)]
fn print_result(n: i32, r: i32) {
  let mut input = String::new();
  let result = String::from("fib(");
;
  print!("{}", result);
  let result = n;
;
  print!("{}", result);
  let result = String::from(") = ");
;
  print!("{}", result);
  let result = r;
;
  print!("{}", result);
  let result = String::from("\n");
;
  print!("{}", result);
}

#[allow(warnings)]
fn fib(x: i32) -> i32 {
  let mut input = String::new();
  if (x <= 1) {
    return x;
  }
  else {
    return     fib(x - 2, ) +     fib(x - 1, );
  }
;
}

#[allow(warnings)]
fn main() {
  let mut input = String::new();
  let mut n: i32 = 0;
;
  let mut m: i32 = 26;
;
  while(n < m) {
    print_result(n,     fib(n, ), );
    n = n + 1;
  }
;
}

