use std::collections::HashSet;
use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut tokens = Vec::new();
    
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        for token in line.split_whitespace() {
            tokens.push(token.to_string());
        }
    }
    
    let mut i = 0;
    let N: usize = tokens[i].parse().unwrap(); i += 1;
    let S: usize = tokens[i].parse().unwrap(); i += 1;
    let Q: usize = tokens[i].parse().unwrap(); i += 1;
    let C: i128 = tokens[i].parse().unwrap(); i += 1;
    let H: i128 = tokens[i].parse().unwrap(); i += 1;
    
    let mut widths = Vec::with_capacity(N);
    for _ in 0..N {
        let cp: u32 = u32::from_str_radix(&tokens[i], 16).unwrap();
        i += 1;
        let w = if cp <= 0x7F { 1 } else if cp <= 0x7FF { 2 } else if cp <= 0xFFFF { 3 } else { 4 };
        widths.push(w as i128);
    }
    
    let mut segment_ends = HashSet::new();
    let mut pos = 0;
    for _ in 0..S {
        pos += tokens[i].parse::<usize>().unwrap();
        i += 1;
        segment_ends.insert(pos);
    }
    
    for _ in 0..Q {
        let L: usize = tokens[i].parse().unwrap(); i += 1;
        let R: usize = tokens[i].parse().unwrap(); i += 1;
        let B: i128 = tokens[i].parse().unwrap(); i += 1;
        
        let mut payload = 0i128;
        let mut wire = 0i128;
        let mut sent = 0usize;
        let mut chunks = 0usize;
        let mut last = 0usize;
        let mut last_payload = 0i128;
        let mut chunk_payload = 0i128;
        
        for p in L..=R {
            let w = widths[p - 1];
            
            if chunk_payload > 0 && chunk_payload + w > C {
                chunks += 1;
                last_payload = chunk_payload;
                chunk_payload = 0;
            }
            
            let cost = if chunk_payload == 0 { H } else { 0 } + w;
            if wire + cost > B {
                break;
            }
            
            wire += cost;
            payload += w;
            chunk_payload += w;
            sent += 1;
            last = p;
            
            if segment_ends.contains(&p) {
                chunks += 1;
                last_payload = chunk_payload;
                chunk_payload = 0;
            }
        }
        
        if chunk_payload > 0 {
            chunks += 1;
            last_payload = chunk_payload;
        }
        
        let cause = if sent == R - L + 1 { "END" } else { "LIMIT" };
        println!("{} {} {} {} {} {} {}", payload, wire, sent, last, chunks, last_payload, cause);
    }
}