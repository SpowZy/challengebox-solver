use std::io::{self, BufRead};

#[derive(Clone)]
struct Version {
    p: usize,
    c: usize,
    d: u64,
    producer_tickets: Vec<Option<usize>>,
    slots: Vec<Option<i64>>,
}

const COMPLETION_MARKER: i64 = i64::MIN;
const MOD: i128 = 1000000007;
const HASH_MULT: i128 = 911382323;

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let _q: usize = parts[1].parse().unwrap();
    
    let mut versions = vec![Version {
        p: 0,
        c: 0,
        d: 0,
        producer_tickets: vec![None; n],
        slots: vec![],
    }];
    
    for _ in 0..(_q) {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        let op = parts[0];
        let b: usize = parts[1].parse().unwrap();
        
        match op {
            "R" => {
                let s: usize = parts[2].parse().unwrap();
                let mut v = versions[b].clone();
                let ticket = v.p;
                v.p += 1;
                v.producer_tickets[s - 1] = Some(ticket);
                versions.push(v);
            }
            "W" => {
                let s: usize = parts[2].parse().unwrap();
                let mut v = versions[b].clone();
                
                let ticket = v.producer_tickets[s - 1].unwrap();
                while v.slots.len() <= ticket {
                    v.slots.push(None);
                }
                
                if parts[3] == "E" {
                    v.slots[ticket] = Some(COMPLETION_MARKER);
                } else {
                    let x: i64 = parts[4].parse().unwrap();
                    v.slots[ticket] = Some(x);
                }
                
                versions.push(v);
            }
            "D" => {
                let k: u64 = parts[2].parse().unwrap();
                let mut v = versions[b].clone();
                v.d += k;
                versions.push(v);
            }
            "P" => {
                let mut v = versions[b].clone();
                let mut m = 0;
                let mut h = 0i128;
                
                loop {
                    if v.c >= v.p {
                        break;
                    }
                    
                    if v.c >= v.slots.len() {
                        break;
                    }
                    
                    match v.slots[v.c] {
                        None => break,
                        Some(COMPLETION_MARKER) => {
                            v.c += 1;
                        }
                        Some(val) => {
                            if v.d == 0 {
                                break;
                            }
                            
                            m += 1;
                            let val_i128 = val as i128;
                            let r = ((val_i128 % MOD) + MOD) % MOD;
                            h = (h * HASH_MULT + r) % MOD;
                            
                            v.c += 1;
                            v.d -= 1;
                        }
                    }
                }
                
                let status = if v.p == v.c && v.c == n {
                    "COMPLETE"
                } else if v.c == v.p && v.p < n {
                    "WAITING"
                } else if v.c < v.p && (v.c >= v.slots.len() || v.slots[v.c].is_none()) {
                    "BLOCKED"
                } else if v.c < v.p && v.slots[v.c].is_some() && v.slots[v.c] != Some(COMPLETION_MARKER) && v.d == 0 {
                    "BACKPRESSURE"
                } else {
                    "UNKNOWN"
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h as i64, status, v.p, v.c, v.d);
                
                versions.push(v);
            }
            _ => {}
        }
    }
}