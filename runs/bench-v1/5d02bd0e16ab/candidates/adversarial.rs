use std::io::{self, BufRead};
use std::collections::HashMap;

#[derive(Clone)]
struct Version {
    p: i64,
    c: i64,
    d: i64,
    slots: Vec<Slot>,
    producer_tickets: Vec<Option<i64>>,
}

#[derive(Clone)]
enum Slot {
    Unpublished,
    Completion,
    Value(i64),
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n = parts[0].parse::<i64>().unwrap();
    let q = parts[1].parse::<i64>().unwrap();
    
    let mut versions = HashMap::new();
    
    let slots = vec![Slot::Unpublished; n as usize];
    let producer_tickets = vec![None; n as usize];
    versions.insert(0, Version {
        p: 0,
        c: 0,
        d: 0,
        slots,
        producer_tickets,
    });
    
    for i in 1..=q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        let b = parts[0].parse::<i64>().unwrap();
        let mut current = versions[&b].clone();
        
        match parts[1] {
            "R" => {
                let s = parts[2].parse::<usize>().unwrap();
                current.producer_tickets[s - 1] = Some(current.p);
                current.p += 1;
            }
            "W" => {
                let s = parts[2].parse::<usize>().unwrap();
                let ticket = current.producer_tickets[s - 1].unwrap() as usize;
                if parts[3] == "E" {
                    current.slots[ticket] = Slot::Completion;
                } else {
                    let x = parts[4].parse::<i64>().unwrap();
                    current.slots[ticket] = Slot::Value(x);
                }
            }
            "D" => {
                let k = parts[2].parse::<i64>().unwrap();
                current.d += k;
            }
            "P" => {
                let mut m = 0i64;
                let mut h = 0i64;
                
                while current.c < current.p {
                    let slot_idx = current.c as usize;
                    match &current.slots[slot_idx] {
                        Slot::Unpublished => break,
                        Slot::Completion => {
                            current.c += 1;
                        }
                        Slot::Value(x) => {
                            if current.d == 0 {
                                break;
                            }
                            m += 1;
                            let r = ((*x % 1000000007) + 1000000007) % 1000000007;
                            h = (h * 911382323 + r) % 1000000007;
                            current.c += 1;
                            current.d -= 1;
                        }
                    }
                }
                
                let status = if current.p == current.c && current.c == n {
                    "COMPLETE"
                } else if current.c == current.p && current.p < n {
                    "WAITING"
                } else if current.c < current.p {
                    if let Slot::Unpublished = &current.slots[current.c as usize] {
                        "BLOCKED"
                    } else {
                        "BACKPRESSURE"
                    }
                } else {
                    "WAITING"
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h, status, current.p, current.c, current.d);
            }
            _ => {}
        }
        
        versions.insert(i, current);
    }
}