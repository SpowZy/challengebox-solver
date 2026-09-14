use std::io::{self, BufRead};
use std::collections::HashMap;

#[derive(Clone)]
enum Slot {
    Unpublished,
    Completion,
    Value(i64),
}

#[derive(Clone)]
struct Version {
    p: usize,
    c: usize,
    d: i128,
    producer_ticket: HashMap<usize, usize>,
    slots: Vec<Slot>,
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let q: usize = parts[1].parse().unwrap();
    
    let mut versions: Vec<Version> = Vec::new();
    
    versions.push(Version {
        p: 0,
        c: 0,
        d: 0,
        producer_ticket: HashMap::new(),
        slots: vec![Slot::Unpublished; n],
    });
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        let op = parts[0];
        let b: usize = parts[1].parse().unwrap();
        
        match op {
            "R" => {
                let s: usize = parts[2].parse().unwrap();
                let mut new_version = versions[b].clone();
                new_version.producer_ticket.insert(s, new_version.p);
                new_version.p += 1;
                versions.push(new_version);
            }
            "W" => {
                let s: usize = parts[2].parse().unwrap();
                let mut new_version = versions[b].clone();
                let ticket = new_version.producer_ticket[&s];
                
                if parts[3] == "E" {
                    new_version.slots[ticket] = Slot::Completion;
                } else {
                    let x: i64 = parts[4].parse().unwrap();
                    new_version.slots[ticket] = Slot::Value(x);
                }
                
                versions.push(new_version);
            }
            "D" => {
                let k: i128 = parts[2].parse().unwrap();
                let mut new_version = versions[b].clone();
                new_version.d += k;
                versions.push(new_version);
            }
            "P" => {
                let mut version = versions[b].clone();
                let mut m = 0;
                let mut h: i64 = 0;
                
                loop {
                    if version.c >= version.p {
                        break;
                    }
                    
                    match version.slots[version.c] {
                        Slot::Unpublished => break,
                        Slot::Completion => {
                            version.c += 1;
                        }
                        Slot::Value(x) => {
                            if version.d > 0 {
                                m += 1;
                                let r = ((x % 1000000007) + 1000000007) % 1000000007;
                                h = ((h as i128 * 911382323 + r as i128) % 1000000007) as i64;
                                version.c += 1;
                                version.d -= 1;
                            } else {
                                break;
                            }
                        }
                    }
                }
                
                let status = if version.c == version.p {
                    if version.p == n {
                        "COMPLETE"
                    } else {
                        "WAITING"
                    }
                } else {
                    match version.slots[version.c] {
                        Slot::Unpublished => "BLOCKED",
                        Slot::Value(_) if version.d == 0 => "BACKPRESSURE",
                        _ => "BLOCKED",
                    }
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h, status, version.p, version.c, version.d);
            }
            _ => {}
        }
    }
}