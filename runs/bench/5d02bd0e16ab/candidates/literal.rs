use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let q: usize = parts[1].parse().unwrap();
    
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
        slots: Vec<SlotState>,
        producer_tickets: Vec<Option<usize>>,
    }
    
    let mut versions = Vec::new();
    
    let initial_slots = vec![SlotState::Unpublished; n];
    let initial_producer_tickets = vec![None; n + 1];
    
    versions.push(Version {
        p: 0,
        c: 0,
        d: 0,
        slots: initial_slots,
        producer_tickets: initial_producer_tickets,
    });
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let op = parts[0];
        let b: usize = parts[1].parse().unwrap();
        
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
                    new_version.slots[ticket] = SlotState::Completion;
                } else {
                    let x: i64 = parts[4].parse().unwrap();
                    new_version.slots[ticket] = SlotState::Value(x);
                }
            }
            "D" => {
                let k: i64 = parts[2].parse().unwrap();
                new_version.d += k;
            }
            "P" => {
                let mut emitted_values = Vec::new();
                let mut temp_c = new_version.c;
                let mut temp_d = new_version.d;
                
                while temp_c < new_version.p {
                    match &new_version.slots[temp_c] {
                        SlotState::Unpublished => break,
                        SlotState::Completion => {
                            temp_c += 1;
                        }
                        SlotState::Value(x) => {
                            if temp_d > 0 {
                                emitted_values.push(*x);
                                temp_c += 1;
                                temp_d -= 1;
                            } else {
                                break;
                            }
                        }
                    }
                }
                
                new_version.c = temp_c;
                new_version.d = temp_d;
                
                let mut h: i64 = 0;
                const MOD: i64 = 1000000007;
                const MUL: i64 = 911382323;
                
                for val in &emitted_values {
                    let r = {
                        let rem = val % MOD;
                        if rem < 0 { rem + MOD } else { rem }
                    };
                    h = (((h as i128 * MUL as i128) + r as i128) % (MOD as i128)) as i64;
                }
                
                let status = if new_version.p == n && new_version.c == n {
                    "COMPLETE"
                } else if new_version.c == new_version.p {
                    "WAITING"
                } else {
                    match &new_version.slots[new_version.c] {
                        SlotState::Unpublished => "BLOCKED",
                        _ => "BACKPRESSURE",
                    }
                };
                
                println!("DRAIN {} {} {} {} {} {}", emitted_values.len(), h, status, new_version.p, new_version.c, new_version.d);
            }
            _ => {}
        }
        
        versions.push(new_version);
    }
}