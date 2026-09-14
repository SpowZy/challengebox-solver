use std::io::{self, BufRead};
use std::collections::HashMap;

#[derive(Clone)]
enum ProducerState {
    Unpublished,
    Completion,
    Value(i64),
}

struct Version {
    p: u64,
    c: u64,
    d: u64,
    producer_reservations: HashMap<usize, usize>,
    slot_changes: HashMap<usize, ProducerState>,
    parent: Option<usize>,
}

fn get_producer_slot(versions: &[Version], version_id: usize, producer_id: usize) -> Option<usize> {
    let mut current = version_id;
    loop {
        if let Some(slot) = versions[current].producer_reservations.get(&producer_id) {
            return Some(*slot);
        }
        if let Some(parent) = versions[current].parent {
            current = parent;
        } else {
            return None;
        }
    }
}

fn get_slot_state(versions: &[Version], version_id: usize, slot: usize) -> ProducerState {
    let mut current = version_id;
    loop {
        if let Some(state) = versions[current].slot_changes.get(&slot) {
            return state.clone();
        }
        if let Some(parent) = versions[current].parent {
            current = parent;
        } else {
            return ProducerState::Unpublished;
        }
    }
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    
    let mut versions = vec![Version {
        p: 0,
        c: 0,
        d: 0,
        producer_reservations: HashMap::new(),
        slot_changes: HashMap::new(),
        parent: None,
    }];
    
    for line in lines {
        let line = line.unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        let op_type = parts[0];
        let b: usize = parts[1].parse().unwrap();
        
        match op_type {
            "R" => {
                let s: usize = parts[2].parse().unwrap();
                let slot = versions[b].p as usize;
                let mut producer_reservations = HashMap::new();
                producer_reservations.insert(s, slot);
                
                versions.push(Version {
                    p: versions[b].p + 1,
                    c: versions[b].c,
                    d: versions[b].d,
                    producer_reservations,
                    slot_changes: HashMap::new(),
                    parent: Some(b),
                });
            }
            "W" => {
                let s: usize = parts[2].parse().unwrap();
                let slot = get_producer_slot(&versions, b, s).unwrap();
                
                let state = if parts[3] == "E" {
                    ProducerState::Completion
                } else {
                    let x: i64 = parts[4].parse().unwrap();
                    ProducerState::Value(x)
                };
                
                let mut slot_changes = HashMap::new();
                slot_changes.insert(slot, state);
                
                versions.push(Version {
                    p: versions[b].p,
                    c: versions[b].c,
                    d: versions[b].d,
                    producer_reservations: HashMap::new(),
                    slot_changes,
                    parent: Some(b),
                });
            }
            "D" => {
                let k: u64 = parts[2].parse().unwrap();
                versions.push(Version {
                    p: versions[b].p,
                    c: versions[b].c,
                    d: versions[b].d + k,
                    producer_reservations: HashMap::new(),
                    slot_changes: HashMap::new(),
                    parent: Some(b),
                });
            }
            "P" => {
                let mut p = versions[b].p;
                let mut c = versions[b].c;
                let mut d = versions[b].d;
                let mut m = 0u64;
                let mut h = 0u64;
                
                while c < p {
                    match get_slot_state(&versions, b, c as usize) {
                        ProducerState::Unpublished => break,
                        ProducerState::Completion => c += 1,
                        ProducerState::Value(x) => {
                            if d > 0 {
                                d -= 1;
                                c += 1;
                                m += 1;
                                let r = (((x % 1000000007) + 1000000007) % 1000000007) as u64;
                                h = (h * 911382323 + r) % 1000000007;
                            } else {
                                break;
                            }
                        }
                    }
                }
                
                let n_u64 = n as u64;
                let status = if p == c && c == n_u64 {
                    "COMPLETE"
                } else if c == p && c < n_u64 {
                    "WAITING"
                } else if c < p {
                    match get_slot_state(&versions, b, c as usize) {
                        ProducerState::Unpublished => "BLOCKED",
                        _ => "BACKPRESSURE",
                    }
                } else {
                    "WAITING"
                };
                
                println!("DRAIN {} {} {} {} {} {}", m, h, status, p, c, d);
            }
            _ => {}
        }
    }
}