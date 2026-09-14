use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let q: usize = parts[1].parse().unwrap();
    
    const MOD: u64 = 1000000007;
    const MULT: u64 = 911382323;
    
    #[derive(Clone)]
    enum Op {
        R { s: usize },
        W { s: usize, v: Option<i64> },
        D { k: u64 },
        P,
    }
    
    let mut ops: Vec<(usize, Op)> = vec![];
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let b: usize = parts[1].parse().unwrap();
        let op = match parts[0] {
            "R" => Op::R { s: parts[2].parse().unwrap() },
            "W" => {
                let s = parts[2].parse().unwrap();
                let v = if parts[3] == "E" { None } else { Some(parts[4].parse().unwrap()) };
                Op::W { s, v }
            }
            "D" => Op::D { k: parts[2].parse().unwrap() },
            "P" => Op::P,
            _ => unreachable!(),
        };
        ops.push((b, op));
    }
    
    for op_idx in 0..ops.len() {
        if let Op::P = ops[op_idx].1 {
            let mut p: u64 = 0;
            let mut c: u64 = 0;
            let mut d: u64 = 0;
            let mut slots: Vec<Option<Option<i64>>> = vec![None; n];
            let mut tickets: Vec<Option<u64>> = vec![None; n];
            
            let mut path = vec![];
            let mut v = op_idx + 1;
            loop {
                path.push(v);
                if v == 0 { break; }
                v = ops[v - 1].0;
            }
            
            path.reverse();
            for pv in path {
                if pv > 0 {
                    match &ops[pv - 1].1 {
                        Op::R { s } => {
                            tickets[s - 1] = Some(p);
                            p += 1;
                        }
                        Op::W { s, v } => {
                            let t = tickets[s - 1].unwrap() as usize;
                            slots[t] = Some(*v);
                        }
                        Op::D { k } => d += k,
                        Op::P => {}
                    }
                }
            }
            
            let mut vals = Vec::new();
            while c < p {
                match slots[c as usize] {
                    None => break,
                    Some(None) => c += 1,
                    Some(Some(x)) => {
                        if d > 0 {
                            vals.push(x);
                            c += 1;
                            d -= 1;
                        } else {
                            break;
                        }
                    }
                }
            }
            
            let mut h: u64 = 0;
            for x in &vals {
                let r = ((((*x as i128) % (MOD as i128)) + (MOD as i128)) % (MOD as i128)) as u64;
                h = (h.wrapping_mul(MULT) + r) % MOD;
            }
            
            let status = if p == c && p == n as u64 {
                "COMPLETE"
            } else if c == p && p < n as u64 {
                "WAITING"
            } else if c < p && slots[c as usize].is_none() {
                "BLOCKED"
            } else {
                "BACKPRESSURE"
            };
            
            println!("DRAIN {} {} {} {} {} {}", vals.len(), h, status, p, c, d);
        }
    }
}