use std::io::{self, BufRead};

#[derive(Clone)]
struct Slot {
    published: bool,
    is_completion: bool,
    value: i64,
}

#[derive(Clone)]
struct Version {
    p: usize,
    c: usize,
    d: u64,
    slots: Vec<Slot>,
    producer_tickets: Vec<Option<usize>>,
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    
    let mut versions: Vec<Version> = Vec::new();
    versions.push(Version {
        p: 0,
        c: 0,
        d: 0,
        slots: vec![Slot { published: false, is_completion: false, value: 0 }; n],
        producer_tickets: vec![None; n + 1],
    });
    
    for line_result in lines {
        if let Ok(line) = line_result {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.is_empty() { break; }
            
            let b: usize = parts[0].parse().unwrap();
            let op = parts[1];
            let mut new_version = versions[b].clone();
            
            match op {
                "R" => {
                    let s: usize = parts[2].parse().unwrap();
                    new_version.producer_tickets[s] = Some(new_version.p);
                    new_version.p += 1;
                }
                "W" => {
                    let s: usize = parts[2].parse().unwrap();
                    let ticket = new_version.producer_tickets[s].unwrap();
                    if parts[3] == "E" {
                        new_version.slots[ticket] = Slot { published: true, is_completion: true, value: 0 };
                    } else {
                        let x: i64 = parts[4].parse().unwrap();
                        new_version.slots[ticket] = Slot { published: true, is_completion: false, value: x };
                    }
                }
                "D" => {
                    let k: u64 = parts[2].parse().unwrap();
                    new_version.d += k;
                }
                "P" => {
                    let mut h: u64 = 0;
                    let mut m: usize = 0;
                    
                    while new_version.c < new_version.p {
                        if !new_version.slots[new_version.c].published {
                            break;
                        }
                        if new_version.slots[new_version.c].is_completion {
                            new_version.c += 1;
                        } else {
                            if new_version.d > 0 {
                                let val = new_version.slots[new_version.c].value;
                                let modulus = 1000000007i64;
                                let mut r = val % modulus;
                                if r < 0 { r += modulus; }
                                h = (((h as u128) * 911382323 + (r as u128)) % 1000000007) as u64;
                                m += 1;
                                new_version.c += 1;
                                new_version.d -= 1;
                            } else {
                                break;
                            }
                        }
                    }
                    
                    let status = if new_version.p == n && new_version.c == n {
                        "COMPLETE"
                    } else if new_version.c == new_version.p && new_version.p < n {
                        "WAITING"
                    } else if new_version.c < new_version.p && !new_version.slots[new_version.c].published {
                        "BLOCKED"
                    } else {
                        "BACKPRESSURE"
                    };
                    
                    println!("DRAIN {} {} {} {} {} {}", m, h, status, new_version.p, new_version.c, new_version.d);
                }
                _ => {}
            }
            
            versions.push(new_version);
        } else {
            break;
        }
    }
}