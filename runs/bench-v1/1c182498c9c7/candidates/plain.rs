fn main() {
    use std::io::{self, BufRead};
    
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    // Parse first line
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let s: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    let c: u64 = parts[3].parse().unwrap();
    let h: u64 = parts[4].parse().unwrap();
    
    // Read characters
    let mut characters = Vec::new();
    while characters.len() < n {
        let line = lines.next().unwrap().unwrap();
        for token in line.split_whitespace() {
            if characters.len() < n {
                let code_point: u32 = u32::from_str_radix(token, 16).unwrap();
                characters.push(code_point);
            }
        }
    }
    
    // Read segment lengths
    let mut segment_lengths = Vec::new();
    while segment_lengths.len() < s {
        let line = lines.next().unwrap().unwrap();
        for token in line.split_whitespace() {
            if segment_lengths.len() < s {
                segment_lengths.push(token.parse::<usize>().unwrap());
            }
        }
    }
    
    // Build segment_at array
    let mut segment_at = vec![0usize; n];
    let mut pos = 0;
    for (seg_idx, &len) in segment_lengths.iter().enumerate() {
        for i in 0..len {
            if pos + i < n {
                segment_at[pos + i] = seg_idx;
            }
        }
        pos += len;
    }
    
    // Process queries
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let l: usize = parts[0].parse().unwrap();
        let r: usize = parts[1].parse().unwrap();
        let b: u64 = parts[2].parse().unwrap();
        
        let l = l - 1;
        let r = r - 1;
        
        let mut payload_bytes = 0u64;
        let mut wire_bytes = 0u64;
        let mut characters_sent = 0u64;
        let mut last = 0usize;
        let mut chunks = 0u64;
        let mut last_chunk_payload = 0u64;
        let mut cause = "END";
        
        let mut current_chunk_payload = 0u64;
        let mut current_segment = segment_at[l];
        
        for pos in l..=r {
            let new_segment = segment_at[pos];
            
            if new_segment != current_segment {
                current_chunk_payload = 0;
                current_segment = new_segment;
            }
            
            let char_width = get_utf8_width(characters[pos]) as u64;
            let starting_new_chunk = current_chunk_payload == 0;
            
            let wire_to_add = if starting_new_chunk {
                char_width.checked_add(h).unwrap_or(u64::MAX)
            } else {
                char_width
            };
            
            if wire_bytes.checked_add(wire_to_add).map_or(true, |sum| sum > b) {
                cause = "LIMIT";
                break;
            }
            
            payload_bytes += char_width;
            wire_bytes += wire_to_add;
            current_chunk_payload += char_width;
            characters_sent += 1;
            last = pos + 1;
            
            if starting_new_chunk {
                chunks += 1;
            }
            
            last_chunk_payload = current_chunk_payload;
            
            if current_chunk_payload >= c {
                current_chunk_payload = 0;
            }
        }
        
        println!("{} {} {} {} {} {} {}", 
                 payload_bytes, wire_bytes, characters_sent, last, chunks, last_chunk_payload, cause);
    }
}

fn get_utf8_width(code_point: u32) -> u8 {
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