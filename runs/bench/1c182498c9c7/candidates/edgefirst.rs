use std::io::{self, BufRead};

fn utf8_width(c: u32) -> u64 {
    match c {
        0..=0x7F => 1,
        0x80..=0x7FF => 2,
        0x800..=0xFFFF => 3,
        _ => 4,
    }
}

fn get_segment(pos: u64, boundaries: &[u64]) -> u64 {
    for (i, &b) in boundaries.iter().enumerate() {
        if pos < b {
            return i as u64;
        }
    }
    boundaries.len() as u64
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let header = lines.next().unwrap().unwrap();
    let parts: Vec<u64> = header.split_whitespace()
        .map(|s| s.parse().unwrap())
        .collect();
    let n = parts[0];
    let s = parts[1];
    let q = parts[2];
    let c = parts[3];
    let h = parts[4];
    
    let mut chars = Vec::new();
    let mut char_count = 0;
    while char_count < n {
        let line = lines.next().unwrap().unwrap();
        for token in line.split_whitespace() {
            if char_count < n {
                chars.push(u32::from_str_radix(token, 16).unwrap());
                char_count += 1;
            }
        }
    }
    
    let mut boundaries = Vec::new();
    let mut pos = 0u64;
    let mut seg_count = 0;
    while seg_count < s {
        let line = lines.next().unwrap().unwrap();
        for token in line.split_whitespace() {
            if seg_count < s {
                pos += token.parse::<u64>().unwrap();
                boundaries.push(pos);
                seg_count += 1;
            }
        }
    }
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<u64> = line.split_whitespace()
            .map(|s| s.parse().unwrap())
            .collect();
        let l = parts[0] - 1;
        let r = parts[1] - 1;
        let b = parts[2];
        
        let mut payload = 0u64;
        let mut wire = 0u64;
        let mut chars_sent = 0u64;
        let mut last = 0u64;
        let mut num_chunks = 0u64;
        let mut last_chunk_size = 0u64;
        
        let mut chunk_payload = 0u64;
        let mut chunk_segment = 0u64;
        let mut in_chunk = false;
        
        let mut cause = "END";
        
        for pos in l..=r {
            let width = utf8_width(chars[pos as usize]);
            let segment = get_segment(pos, &boundaries);
            
            let need_new_chunk = !in_chunk || segment != chunk_segment || chunk_payload + width > c;
            
            let new_payload = payload + width;
            let new_chunks = if need_new_chunk { num_chunks + 1 } else { num_chunks };
            let new_wire: u128 = (new_payload as u128) + ((new_chunks as u128) * (h as u128));
            
            if new_wire > (b as u128) {
                cause = "LIMIT";
                break;
            }
            
            payload = new_payload;
            wire = new_wire as u64;
            chars_sent += 1;
            last = pos + 1;
            num_chunks = new_chunks;
            
            if need_new_chunk {
                chunk_payload = width;
                chunk_segment = segment;
                in_chunk = true;
            } else {
                chunk_payload += width;
            }
            last_chunk_size = chunk_payload;
        }
        
        if chars_sent == 0 {
            last_chunk_size = 0;
        }
        
        println!("{} {} {} {} {} {} {}", payload, wire, chars_sent, last, num_chunks, last_chunk_size, cause);
    }
}