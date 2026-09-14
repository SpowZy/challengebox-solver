use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let q: usize = parts[1].parse().unwrap();
    
    #[derive(Clone)]
    struct Slot {
        published: bool,
        is_completion: bool,
        value: i64,
    }
    
    #[derive(Clone)]
    struct Version {
        p: u32,
        c: u32,
        d: i64,
    }
    
    let mut slots: Vec<Slot> = vec![Slot { published: false, is_completion: false, value: 0 }; n];
    let mut versions: Vec<Version> = vec![Version { p: 0, c: 0, d: 0 }];
    let mut producer_slot: Vec<Option<usize>> = vec![None; n + 1];
    
    const MOD: i64 = 1000000007;
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let tokens: Vec<&str> = line.split_whitespace().collect();
        
        let op = tokens[0];
        let b: usize = tokens[1].parse().unwrap();
        let mut new_version = versions[b].clone();
        
        match op {
            "R" => {
                let s: usize = tokens[2].parse().unwrap();
                producer_slot[s] = Some(new_version.p as usize);
                new_version.p += 1;
            }
            "W" => {
                let s: usize = tokens[2].parse().unwrap();
                let slot_idx = producer_slot[s].unwrap();
                if tokens[3] == "E" {
                    slots[slot_idx].published = true;
                    slots[slot_idx].is_completion = true;
                } else {
                    let x: i64 = tokens[4].parse().unwrap();
                    slots[slot_idx].published = true;
                    slots[slot_idx].is_completion = false;
                    slots[slot_idx].value = x;
                }
            }
            "D" => {
                let k: i64 = tokens[2].parse().unwrap();
                new_version.d += k;
            }
            "P" => {
                let mut h: i64 = 0;
                let mut m: i64 = 0;
                let mut c = new_version.c;
                let mut d = new_version.d;
                
                while c < new_version.p {
                    if !slots[c as usize].published {
                        break;
                    }
                    if slots[c as usize].is_completion {
                        c += 1;
                    } else {
                        if d > 0 {
                            let val = slots[c as usize].value;
                            let r = ((val % MOD) + MOD) % MOD;
                            h = (h * 911382323 + r) % MOD;
                            m += 1;
                            c += 1;
                            d -= 1;
                        } else {
                            break;
                        }
                    }
                }
                
                new_version.c = c;
                new_version.d = d;
                
                let status = if new_version.p == new_version.c && new_version.c == n as u32 {
                    "COMPLETE"
                } else if new_version.c == new_version.p && new_version.p < n as u32 {
                    "WAITING"
                } else if new_version.c < new_version.p && !slots[new_version.c as usize].published {
                    "BLOCKED"
                } else {
                    "BACKPRESSURE"
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h, status, new_version.p, new_version.c, new_version.d);
            }
            _ => {}
        }
        
        versions.push(new_version);
    }
}