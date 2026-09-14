use std::collections::HashMap;
use std::io::{self, BufRead};

#[derive(Clone)]
enum SlotState {
    Unpublished,
    Completion,
    Value(i64),
}

#[derive(Clone)]
struct Version {
    p: usize,
    c: usize,
    d: i64,
    producer_ticket: HashMap<usize, usize>,
    slot_state: HashMap<usize, SlotState>,
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    
    let mut versions: HashMap<usize, Version> = HashMap::new();
    
    versions.insert(0, Version {
        p: 0,
        c: 0,
        d: 0,
        producer_ticket: HashMap::new(),
        slot_state: HashMap::new(),
    });
    
    let mut op_index = 1;
    for line in lines {
        let line = line.unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        let op = parts[0];
        let b: usize = parts[1].parse().unwrap();
        
        let prev = versions[&b].clone();
        let mut curr = prev;
        
        match op {
            "R" => {
                let s: usize = parts[2].parse().unwrap();
                let ticket = curr.p;
                curr.p += 1;
                curr.producer_ticket.insert(s, ticket);
                curr.slot_state.insert(ticket, SlotState::Unpublished);
            }
            "W" => {
                let s: usize = parts[2].parse().unwrap();
                let ticket = curr.producer_ticket[&s];
                if parts[3] == "E" {
                    curr.slot_state.insert(ticket, SlotState::Completion);
                } else {
                    let x: i64 = parts[4].parse().unwrap();
                    curr.slot_state.insert(ticket, SlotState::Value(x));
                }
            }
            "D" => {
                let k: i64 = parts[2].parse().unwrap();
                curr.d += k;
            }
            "P" => {
                let mut m = 0u64;
                let mut h: u64 = 0;
                const MODULUS: u64 = 1000000007;
                
                while curr.c < curr.p {
                    match curr.slot_state.get(&curr.c) {
                        None | Some(SlotState::Unpublished) => break,
                        Some(SlotState::Completion) => {
                            curr.c += 1;
                        }
                        Some(SlotState::Value(x)) => {
                            if curr.d > 0 {
                                let r = {
                                    let rem = *x % (MODULUS as i64);
                                    if rem < 0 { (rem + MODULUS as i64) as u64 } else { rem as u64 }
                                };
                                h = (h.wrapping_mul(911382323).wrapping_add(r)) % MODULUS;
                                curr.d -= 1;
                                curr.c += 1;
                                m += 1;
                            } else {
                                break;
                            }
                        }
                    }
                }
                
                let status = if curr.p == n && curr.c == n {
                    "COMPLETE"
                } else if curr.c == curr.p && curr.p < n {
                    "WAITING"
                } else if curr.c < curr.p {
                    if matches!(curr.slot_state.get(&curr.c), None | Some(SlotState::Unpublished)) {
                        "BLOCKED"
                    } else {
                        "BACKPRESSURE"
                    }
                } else {
                    "WAITING"
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h, status, curr.p, curr.c, curr.d);
            }
            _ => {}
        }
        
        versions.insert(op_index, curr);
        op_index += 1;
    }
}