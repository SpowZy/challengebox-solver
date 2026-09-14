use std::io::{self, BufRead};
use std::collections::HashMap;

#[derive(Clone)]
enum SlotValue {
    Unpublished,
    Completion,
    Value(i64),
}

#[derive(Clone)]
struct Version {
    p: usize,
    c: usize,
    d: u64,
    reserved: HashMap<usize, usize>,
    slots: Vec<SlotValue>,
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n = parts[0].parse::<usize>().unwrap();
    let q = parts[1].parse::<usize>().unwrap();
    
    let mut versions = vec![];
    versions.push(Version {
        p: 0,
        c: 0,
        d: 0,
        reserved: HashMap::new(),
        slots: vec![],
    });
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        let op = parts[0];
        let b = parts[1].parse::<usize>().unwrap();
        
        let mut v = versions[b].clone();
        
        match op {
            "R" => {
                let s = parts[2].parse::<usize>().unwrap();
                v.reserved.insert(s, v.p);
                while v.slots.len() <= v.p {
                    v.slots.push(SlotValue::Unpublished);
                }
                v.p += 1;
            }
            "W" => {
                let s = parts[2].parse::<usize>().unwrap();
                let ticket = v.reserved[&s];
                if parts[3] == "E" {
                    v.slots[ticket] = SlotValue::Completion;
                } else {
                    let x = parts[4].parse::<i64>().unwrap();
                    v.slots[ticket] = SlotValue::Value(x);
                }
            }
            "D" => {
                let k = parts[2].parse::<u64>().unwrap();
                v.d += k;
            }
            "P" => {
                let mut h = 0u64;
                let mut m = 0u64;
                
                while v.c < v.p {
                    match &v.slots[v.c] {
                        SlotValue::Unpublished => {
                            break;
                        }
                        SlotValue::Completion => {
                            v.c += 1;
                        }
                        SlotValue::Value(value) => {
                            if v.d > 0 {
                                let mut r = value % 1000000007i64;
                                if r < 0 {
                                    r += 1000000007i64;
                                }
                                h = (h * 911382323 + r as u64) % 1000000007;
                                v.d -= 1;
                                m += 1;
                                v.c += 1;
                            } else {
                                break;
                            }
                        }
                    }
                }
                
                let status = if v.p == v.c && v.c == n {
                    "COMPLETE"
                } else if v.c == v.p && v.p < n {
                    "WAITING"
                } else if v.c < v.p {
                    match &v.slots[v.c] {
                        SlotValue::Unpublished => "BLOCKED",
                        _ => "BACKPRESSURE",
                    }
                } else {
                    "WAITING"
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h, status, v.p, v.c, v.d);
            }
            _ => {}
        }
        
        versions.push(v);
    }
}