use std::io::{self, BufRead};

#[derive(Clone)]
enum SlotStatus {
    Unpublished,
    Completion,
    Value(i64),
}

#[derive(Clone)]
struct Version {
    p: usize,
    c: usize,
    d: u64,
    producer_ticket: Vec<Option<usize>>,
    slot_status: Vec<SlotStatus>,
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let q: usize = parts[1].parse().unwrap();
    
    let mut versions = vec![
        Version {
            p: 0,
            c: 0,
            d: 0,
            producer_ticket: vec![None; n],
            slot_status: vec![SlotStatus::Unpublished; n],
        }
    ];
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let op = parts[0];
        let b: usize = parts[1].parse().unwrap();
        
        let parent = &versions[b];
        let mut new_version = parent.clone();
        
        match op {
            "R" => {
                let s: usize = parts[2].parse().unwrap();
                new_version.producer_ticket[s - 1] = Some(new_version.p);
                new_version.p += 1;
            }
            "W" => {
                let s: usize = parts[2].parse().unwrap();
                let ticket = new_version.producer_ticket[s - 1].unwrap();
                if parts[3] == "E" {
                    new_version.slot_status[ticket] = SlotStatus::Completion;
                } else {
                    let x: i64 = parts[4].parse().unwrap();
                    new_version.slot_status[ticket] = SlotStatus::Value(x);
                }
            }
            "D" => {
                let k: u64 = parts[2].parse().unwrap();
                new_version.d += k;
            }
            "P" => {
                let mut m = 0;
                let mut h = 0i64;
                
                while new_version.c < new_version.p {
                    match &new_version.slot_status[new_version.c] {
                        SlotStatus::Unpublished => break,
                        SlotStatus::Completion => {
                            new_version.c += 1;
                        }
                        SlotStatus::Value(x) => {
                            if new_version.d > 0 {
                                let r = x.rem_euclid(1000000007);
                                let h_new = ((h as i128) * 911382323 + r as i128) % 1000000007i128;
                                h = h_new as i64;
                                m += 1;
                                new_version.d -= 1;
                                new_version.c += 1;
                            } else {
                                break;
                            }
                        }
                    }
                }
                
                let status = if new_version.p == n && new_version.c == n {
                    "COMPLETE"
                } else if new_version.c == new_version.p && new_version.p < n {
                    "WAITING"
                } else if new_version.c < new_version.p {
                    match &new_version.slot_status[new_version.c] {
                        SlotStatus::Unpublished => "BLOCKED",
                        SlotStatus::Value(_) if new_version.d == 0 => "BACKPRESSURE",
                        _ => "UNKNOWN",
                    }
                } else {
                    "UNKNOWN"
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h, status, new_version.p, new_version.c, new_version.d);
            }
            _ => {}
        }
        
        versions.push(new_version);
    }
}