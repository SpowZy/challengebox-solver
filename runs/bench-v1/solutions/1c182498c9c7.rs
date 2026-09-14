fn main() {
    use std::io::{self, BufRead};
    use std::collections::HashSet;
    
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let s: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    let c: i64 = parts[3].parse().unwrap();
    let h: i64 = parts[4].parse().unwrap();
    
    let mut chars = Vec::new();
    let mut remaining = n;
    while remaining > 0 {
        let line = lines.next().unwrap().unwrap();
        for token in line.split_whitespace() {
            let code: u32 = u32::from_str_radix(token, 16).unwrap();
            chars.push(code);
            remaining -= 1;
            if remaining == 0 { break; }
        }
    }
    
    let mut segment_ends = Vec::new();
    let mut pos = 0;
    let mut remaining = s;
    while remaining > 0 {
        let line = lines.next().unwrap().unwrap();
        for token in line.split_whitespace() {
            let len: usize = token.parse().unwrap();
            pos += len;
            segment_ends.push(pos);
            remaining -= 1;
            if remaining == 0 { break; }
        }
    }
    
    let segment_boundary_set: HashSet<usize> = segment_ends.into_iter().collect();
    
    let mut byte_widths = Vec::new();
    for &code in &chars {
        let width = if code <= 0x7F { 1 } else if code <= 0x7FF { 2 } else if code <= 0xFFFF { 3 } else { 4 };
        byte_widths.push(width as i64);
    }
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let l: usize = parts[0].parse().unwrap();
        let r: usize = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let mut payload_bytes: i64 = 0;
        let mut wire_bytes: i64 = 0;
        let mut char_count: i64 = 0;
        let mut last: usize = 0;
        let mut chunks: i64 = 0;
        let mut last_chunk_payload: i64 = 0;
        let mut cause = "END";
        
        let mut chunk_payload: i64 = 0;
        
        for i in l..=r {
            let char_idx = i - 1;
            let width = byte_widths[char_idx];
            
            let at_segment_boundary = i > 1 && segment_boundary_set.contains(&(i - 1));
            let starts_new_chunk = (i == l) || (chunk_payload + width > c) || at_segment_boundary;
            
            let header_cost = if starts_new_chunk { h } else { 0 };
            let total_cost = width + header_cost;
            
            if wire_bytes + total_cost > b {
                cause = "LIMIT";
                break;
            }
            
            if starts_new_chunk {
                chunks += 1;
                chunk_payload = width;
                wire_bytes += h;
            } else {
                chunk_payload += width;
            }
            
            payload_bytes += width;
            wire_bytes += width;
            char_count += 1;
            last = i;
            last_chunk_payload = chunk_payload;
        }
        
        println!("{} {} {} {} {} {} {}", payload_bytes, wire_bytes, char_count, last, chunks, last_chunk_payload, cause);
    }
}