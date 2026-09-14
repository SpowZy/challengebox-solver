use std::io::{self, BufRead};

#[derive(Clone)]
struct Version {
    n: usize,
    p: usize,
    c: usize,
    d: u64,
    producer_slot: Vec<Option<usize>>,
    slots: Vec<Option<Slot>>,
}

#[derive(Clone)]
struct Slot {
    published: bool,
    is_completion: bool,
    value: i64,
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let q: usize = parts[1].parse().unwrap();
    
    let mut versions: Vec<Version> = Vec::new();
    
    let v0 = Version {
        n,
        p: 0,
        c: 0,
        d: 0,
        producer_slot: vec![None; n + 1],
        slots: vec![None; n],
    };
    versions.push(v0);
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let op = parts[0];
        let b: usize = parts[1].parse().unwrap();
        
        let mut new_version = versions[b].clone();
        
        match op {
            "R" => {
                let s: usize = parts[2].parse().unwrap();
                new_version.producer_slot[s] = Some(new_version.p);
                new_version.slots[new_version.p] = Some(Slot {
                    published: false,
                    is_completion: false,
                    value: 0,
                });
                new_version.p += 1;
            }
            "W" => {
                let s: usize = parts[2].parse().unwrap();
                let slot_idx = new_version.producer_slot[s].unwrap();
                if parts[3] == "E" {
                    new_version.slots[slot_idx] = Some(Slot {
                        published: true,
                        is_completion: true,
                        value: 0,
                    });
                } else {
                    let x: i64 = parts[4].parse().unwrap();
                    new_version.slots[slot_idx] = Some(Slot {
                        published: true,
                        is_completion: false,
                        value: x,
                    });
                }
            }
            "D" => {
                let k: u64 = parts[2].parse().unwrap();
                new_version.d += k;
            }
            "P" => {
                let mut h: u64 = 0;
                let mut count: usize = 0;
                
                loop {
                    if new_version.c >= new_version.p {
                        break;
                    }
                    
                    if let Some(slot) = &new_version.slots[new_version.c] {
                        if !slot.published {
                            break;
                        }
                        
                        if slot.is_completion {
                            new_version.c += 1;
                        } else {
                            if new_version.d > 0 {
                                let val = slot.value;
                                let r = ((val % 1000000007i64) + 1000000007i64) % 1000000007i64;
                                h = (h * 911382323 + r as u64) % 1000000007;
                                count += 1;
                                new_version.c += 1;
                                new_version.d -= 1;
                            } else {
                                break;
                            }
                        }
                    } else {
                        break;
                    }
                }
                
                let status = if new_version.c == new_version.p {
                    if new_version.p == n {
                        "COMPLETE"
                    } else {
                        "WAITING"
                    }
                } else if new_version.c < new_version.p {
                    if let Some(slot) = &new_version.slots[new_version.c] {
                        if !slot.published {
                            "BLOCKED"
                        } else {
                            "BACKPRESSURE"
                        }
                    } else {
                        "BLOCKED"
                    }
                } else {
                    "COMPLETE"
                };
                
                println!("DRAIN {} {} {} {} {} {}", count, h, status, new_version.p, new_version.c, new_version.d);
            }
            _ => {}
        }
        
        versions.push(new_version);
    }
}