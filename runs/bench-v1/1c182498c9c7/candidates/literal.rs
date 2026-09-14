use std::io::{self, BufRead};

fn utf8_bytes(codepoint: u32) -> u32 {
    if codepoint <= 0x7F {
        1
    } else if codepoint <= 0x7FF {
        2
    } else if codepoint <= 0xFFFF {
        3
    } else {
        4
    }
}

fn get_segment_idx(pos: usize, segment_starts: &[usize]) -> usize {
    for (i, &start) in segment_starts.iter().enumerate().rev() {
        if pos >= start {
            return i;
        }
    }
    0
}

fn main() {
    let stdin = io::stdin();
    let mut input = String::new();
    let mut handle = stdin.lock();
    
    while let Ok(n) = handle.read_line(&mut input) {
        if n == 0 {
            break;
        }
    }
    
    let mut tokens = input.split_whitespace();
    
    let n: usize = tokens.next().unwrap().parse().unwrap();
    let s: usize = tokens.next().unwrap().parse().unwrap();
    let q: usize = tokens.next().unwrap().parse().unwrap();
    let c: u64 = tokens.next().unwrap().parse().unwrap();
    let h: u64 = tokens.next().unwrap().parse().unwrap();
    
    let mut chars = Vec::new();
    for _ in 0..n {
        let c_hex: String = tokens.next().unwrap().to_string();
        let c_val: u32 = u32::from_str_radix(&c_hex, 16).unwrap();
        chars.push(c_val);
    }
    
    let char_sizes: Vec<u64> = chars.iter()
        .map(|&c| utf8_bytes(c) as u64)
        .collect();
    
    let mut segment_lengths = Vec::new();
    for _ in 0..s {
        let seg_len: usize = tokens.next().unwrap().parse().unwrap();
        segment_lengths.push(seg_len);
    }
    
    let mut segment_starts = vec![0];
    let mut pos = 0;
    for &len in segment_lengths.iter().take(s-1) {
        pos += len;
        segment_starts.push(pos);
    }
    
    for _ in 0..q {
        let l: usize = tokens.next().unwrap().parse().unwrap();
        let r: usize = tokens.next().unwrap().parse().unwrap();
        let b: u64 = tokens.next().unwrap().parse().unwrap();
        
        let l_idx = l - 1;
        let r_idx = r - 1;
        
        let mut payload_bytes = 0u64;
        let mut wire_bytes = 0u64;
        let mut characters = 0u64;
        let mut last = 0usize;
        let mut chunks = 0u64;
        let mut last_chunk_payload = 0u64;
        
        let mut current_chunk_payload = 0u64;
        let mut pos = l_idx;
        let mut last_segment_idx = get_segment_idx(l_idx, &segment_starts);
        
        while pos <= r_idx {
            let current_segment_idx = get_segment_idx(pos, &segment_starts);
            
            if current_segment_idx != last_segment_idx {
                if current_chunk_payload > 0 {
                    chunks += 1;
                    last_chunk_payload = current_chunk_payload;
                    current_chunk_payload = 0;
                }
                last_segment_idx = current_segment_idx;
            }
            
            let char_size = char_sizes[pos];
            
            let mut will_start_new_chunk = false;
            if current_chunk_payload == 0 {
                will_start_new_chunk = true;
            } else if current_chunk_payload + char_size > c {
                chunks += 1;
                last_chunk_payload = current_chunk_payload;
                current_chunk_payload = 0;
                will_start_new_chunk = true;
            }
            
            let wire_needed = char_size + if will_start_new_chunk { h } else { 0 };
            
            if let Some(new_wire_bytes) = wire_bytes.checked_add(wire_needed) {
                if new_wire_bytes > b {
                    break;
                }
                wire_bytes = new_wire_bytes;
            } else {
                break;
            }
            
            payload_bytes += char_size;
            current_chunk_payload += char_size;
            characters += 1;
            last = pos + 1;
            
            pos += 1;
        }
        
        if current_chunk_payload > 0 {
            chunks += 1;
            last_chunk_payload = current_chunk_payload;
        }
        
        let cause = if last == r { "END" } else { "LIMIT" };
        
        println!("{} {} {} {} {} {} {}", 
            payload_bytes, wire_bytes, characters, last, chunks, 
            last_chunk_payload, cause);
    }
}