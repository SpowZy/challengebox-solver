use std::io::Read;

fn main() {
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).unwrap();
    
    let tokens: Vec<&str> = input.split_whitespace().collect();
    let mut idx = 0;
    
    let n: usize = tokens[idx].parse().unwrap(); idx += 1;
    let s: usize = tokens[idx].parse().unwrap(); idx += 1;
    let q: usize = tokens[idx].parse().unwrap(); idx += 1;
    let c: u64 = tokens[idx].parse().unwrap(); idx += 1;
    let h: u64 = tokens[idx].parse().unwrap(); idx += 1;
    
    let mut chars = Vec::new();
    for _ in 0..n {
        let val: u32 = u32::from_str_radix(tokens[idx], 16).unwrap();
        chars.push(val);
        idx += 1;
    }
    
    let mut segment_ends = Vec::new();
    let mut pos = 0;
    for _ in 0..s {
        let len: usize = tokens[idx].parse().unwrap();
        idx += 1;
        pos += len;
        segment_ends.push(pos);
    }
    
    fn utf8_bytes(ch: u32) -> u64 {
        if ch <= 0x7F { 1 } else if ch <= 0x7FF { 2 } else if ch <= 0xFFFF { 3 } else { 4 }
    }
    
    fn get_segment_end(pos: usize, segment_ends: &[usize]) -> usize {
        for &end in segment_ends {
            if pos <= end { return end; }
        }
        segment_ends[segment_ends.len() - 1]
    }
    
    for _ in 0..q {
        let l: usize = tokens[idx].parse().unwrap(); idx += 1;
        let r: usize = tokens[idx].parse().unwrap(); idx += 1;
        let b: u64 = tokens[idx].parse().unwrap(); idx += 1;
        
        let mut payload_bytes: u64 = 0;
        let mut wire_bytes: u64 = 0;
        let mut characters: usize = 0;
        let mut last: usize = 0;
        let mut chunks: usize = 0;
        let mut last_chunk_payload: u64 = 0;
        let mut cause = "LIMIT";
        
        let mut current_chunk_payload: u64 = 0;
        let mut current_segment_end: usize = 0;
        let mut first_char = true;
        
        for pos in l..=r {
            let ch = chars[pos - 1];
            let ch_bytes = utf8_bytes(ch);
            let segment_end = get_segment_end(pos, &segment_ends);
            
            let need_new_chunk = first_char ||
                                 current_chunk_payload + ch_bytes > c ||
                                 segment_end != current_segment_end;
            
            let header_bytes = if need_new_chunk { h } else { 0 };
            
            if wire_bytes + header_bytes + ch_bytes > b {
                break;
            }
            
            if need_new_chunk {
                chunks += 1;
                current_chunk_payload = ch_bytes;
                wire_bytes += h + ch_bytes;
                current_segment_end = segment_end;
                first_char = false;
            } else {
                current_chunk_payload += ch_bytes;
                wire_bytes += ch_bytes;
            }
            
            payload_bytes += ch_bytes;
            characters += 1;
            last = pos;
            last_chunk_payload = current_chunk_payload;
            
            if pos == r {
                cause = "END";
            }
        }
        
        println!("{} {} {} {} {} {} {}", 
                 payload_bytes, wire_bytes, characters, last, chunks, last_chunk_payload, cause);
    }
}