use std::io::{self, BufRead};

fn utf8_size(code_point: u32) -> u64 {
    if code_point <= 0x7F {
        1
    } else if code_point <= 0x7FF {
        2
    } else if code_point <= 0xFFFF {
        3
    } else {
        4
    }
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let s: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    let c: u64 = parts[3].parse().unwrap();
    let h: u64 = parts[4].parse().unwrap();
    
    let char_line = lines.next().unwrap().unwrap();
    let char_tokens: Vec<&str> = char_line.split_whitespace().collect();
    let characters: Vec<u32> = char_tokens.iter()
        .map(|token| u32::from_str_radix(token, 16).unwrap())
        .collect();
    
    let seg_line = lines.next().unwrap().unwrap();
    let seg_tokens: Vec<&str> = seg_line.split_whitespace().collect();
    let mut segment_ends = Vec::new();
    let mut sum = 0;
    for (i, token) in seg_tokens.iter().enumerate() {
        if i >= s {
            break;
        }
        let len: usize = token.parse().unwrap();
        sum += len;
        segment_ends.push(sum);
    }
    
    let mut pos_to_segment = vec![0; n + 1];
    let mut seg_idx = 0;
    for pos in 1..=n {
        while seg_idx < segment_ends.len() && pos > segment_ends[seg_idx] {
            seg_idx += 1;
        }
        pos_to_segment[pos] = seg_idx;
    }
    
    for _ in 0..q {
        let req_line = lines.next().unwrap().unwrap();
        let req_parts: Vec<&str> = req_line.split_whitespace().collect();
        let l: usize = req_parts[0].parse().unwrap();
        let r: usize = req_parts[1].parse().unwrap();
        let b: u64 = req_parts[2].parse().unwrap();
        
        let mut payload_bytes: u64 = 0;
        let mut wire_bytes: u64 = 0;
        let mut num_chunks: u64 = 0;
        let mut last_pos: usize = 0;
        let mut current_chunk_payload: u64 = 0;
        let mut cause = "LIMIT";
        
        for pos in l..=r {
            let char_size = utf8_size(characters[pos - 1]);
            
            let starts_new_chunk = if num_chunks == 0 {
                true
            } else if current_chunk_payload + char_size > c {
                true
            } else if pos > l && pos_to_segment[pos] != pos_to_segment[pos - 1] {
                true
            } else {
                false
            };
            
            let header_cost = if starts_new_chunk { h } else { 0 };
            if wire_bytes + header_cost + char_size > b {
                break;
            }
            
            if starts_new_chunk {
                wire_bytes += h;
                num_chunks += 1;
                current_chunk_payload = 0;
            }
            
            payload_bytes += char_size;
            wire_bytes += char_size;
            current_chunk_payload += char_size;
            last_pos = pos;
        }
        
        if last_pos == r {
            cause = "END";
        }
        
        let character_count = if last_pos > 0 { last_pos - l + 1 } else { 0 };
        let last_chunk_payload = if last_pos > 0 { current_chunk_payload } else { 0 };
        
        println!("{} {} {} {} {} {} {}", 
                 payload_bytes, wire_bytes, character_count, last_pos, 
                 num_chunks, last_chunk_payload, cause);
    }
}