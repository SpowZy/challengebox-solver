use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let q: usize = parts[1].parse().unwrap();
    
    #[derive(Clone)]
    struct Version {
        p: usize,
        c: usize,
        d: u64,
        published: Vec<Option<Option<i64>>>,
        producer_tickets: Vec<Option<usize>>,
    }
    
    let mut versions = vec![];
    
    let v0 = Version {
        p: 0,
        c: 0,
        d: 0,
        published: vec![None; n],
        producer_tickets: vec![None; n],
    };
    versions.push(v0);
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        let op = parts[0];
        let b: usize = parts[1].parse().unwrap();
        
        let mut version = versions[b].clone();
        
        match op {
            "R" => {
                let s: usize = parts[2].parse().unwrap();
                let s_idx = s - 1;
                version.producer_tickets[s_idx] = Some(version.p);
                version.p += 1;
            }
            "W" => {
                let s: usize = parts[2].parse().unwrap();
                let s_idx = s - 1;
                let ticket = version.producer_tickets[s_idx].unwrap();
                if parts[3] == "E" {
                    version.published[ticket] = Some(None);
                } else {
                    let x: i64 = parts[4].parse().unwrap();
                    version.published[ticket] = Some(Some(x));
                }
            }
            "D" => {
                let k: u64 = parts[2].parse().unwrap();
                version.d += k;
            }
            "P" => {
                let mut m = 0;
                let mut h: u64 = 0;
                
                while version.c < version.p {
                    if let Some(slot) = version.published[version.c] {
                        if let Some(x) = slot {
                            if version.d > 0 {
                                m += 1;
                                let r = {
                                    let mod_val = x % 1000000007i64;
                                    let adjusted = mod_val + 1000000007i64;
                                    (adjusted % 1000000007i64) as u64
                                };
                                let prod = (h as u128) * 911382323u128;
                                let sum = prod + (r as u128);
                                h = (sum % 1000000007u128) as u64;
                                version.c += 1;
                                version.d -= 1;
                            } else {
                                break;
                            }
                        } else {
                            m += 1;
                            version.c += 1;
                        }
                    } else {
                        break;
                    }
                }
                
                let status = if version.p == n && version.c == n {
                    "COMPLETE"
                } else if version.c == version.p && version.p < n {
                    "WAITING"
                } else if version.c < version.p && version.published[version.c].is_none() {
                    "BLOCKED"
                } else {
                    "BACKPRESSURE"
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h, status, version.p, version.c, version.d);
            }
            _ => {}
        }
        
        versions.push(version);
    }
}