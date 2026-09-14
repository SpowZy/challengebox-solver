use std::io::{self, BufRead};

#[derive(Clone)]
struct Version {
    p: usize,
    c: usize,
    d: i64,
    slots: Vec<Option<Option<i64>>>,
    producer_tickets: Vec<Option<usize>>,
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let q: usize = parts[1].parse().unwrap();
    
    let mut versions: Vec<Version> = vec![Version {
        p: 0,
        c: 0,
        d: 0,
        slots: vec![None; n],
        producer_tickets: vec![None; n],
    }];
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let tokens: Vec<&str> = line.split_whitespace().collect();
        let cmd = tokens[0];
        let b: usize = tokens[1].parse().unwrap();
        
        let mut base_version = versions[b].clone();
        
        match cmd {
            "R" => {
                let s: usize = tokens[2].parse().unwrap();
                base_version.producer_tickets[s - 1] = Some(base_version.p);
                base_version.p += 1;
                versions.push(base_version);
            }
            "W" => {
                let s: usize = tokens[2].parse().unwrap();
                let ticket = base_version.producer_tickets[s - 1].unwrap();
                if tokens[3] == "E" {
                    base_version.slots[ticket] = Some(None);
                } else if tokens[3] == "V" {
                    let x: i64 = tokens[4].parse().unwrap();
                    base_version.slots[ticket] = Some(Some(x));
                }
                versions.push(base_version);
            }
            "D" => {
                let k: i64 = tokens[2].parse().unwrap();
                base_version.d += k;
                versions.push(base_version);
            }
            "P" => {
                let mut m = 0;
                let mut h: i64 = 0;
                
                loop {
                    if base_version.c >= base_version.p {
                        break;
                    }
                    
                    match base_version.slots[base_version.c] {
                        None => {
                            break;
                        }
                        Some(None) => {
                            base_version.c += 1;
                        }
                        Some(Some(x)) => {
                            if base_version.d > 0 {
                                m += 1;
                                let r = ((x % 1000000007) + 1000000007) % 1000000007;
                                h = (h * 911382323 + r) % 1000000007;
                                base_version.c += 1;
                                base_version.d -= 1;
                            } else {
                                break;
                            }
                        }
                    }
                }
                
                let status = if base_version.p == base_version.c && base_version.c == n {
                    "COMPLETE"
                } else if base_version.c == base_version.p && base_version.p < n {
                    "WAITING"
                } else if base_version.c < base_version.p && base_version.slots[base_version.c].is_none() {
                    "BLOCKED"
                } else {
                    "BACKPRESSURE"
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h, status, base_version.p, base_version.c, base_version.d);
                
                versions.push(base_version);
            }
            _ => {}
        }
    }
}