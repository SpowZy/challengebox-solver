use std::io::Read;

fn utf8_width(code_point: u32) -> u64 {
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
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).unwrap();
    
    let mut tokens = input.split_whitespace();
    
    let n: usize = tokens.next().unwrap().parse().unwrap();
    let s: usize = tokens.next().unwrap().parse().unwrap();
    let q: usize = tokens.next().unwrap().parse().unwrap();
    let c: u64 = tokens.next().unwrap().parse().unwrap();
    let h: u64 = tokens.next().unwrap().parse().unwrap();
    
    let mut characters = Vec::new();
    for _ in 0..n {
        let char_hex = tokens.next().unwrap();
        let code_point = u32::from_str_radix(char_hex, 16).unwrap();
        characters.push(code_point);
    }
    
    let mut segment_ends = Vec::new();
    let mut pos = 0;
    for _ in 0..s {
        let len: usize = tokens.next().unwrap().parse().unwrap();
        pos += len;
        segment_ends.push(pos);
    }
    
    for _ in 0..q {
        let l: usize = tokens.next().unwrap().parse().unwrap();
        let r: usize = tokens.next().unwrap().parse().unwrap();
        let b: u64 = tokens.next().unwrap().parse().unwrap();
        
        let mut total_payload = 0u64;
        let mut total_wire = 0u64;
        let mut chunk_count = 0u64;
        let mut current_chunk_payload = 0u64;
        let mut last_chunk_payload = 0u64;
        let mut last_pos = 0usize;
        let mut cause = "END";
        
        for pos in l..=r {
            let char_width = utf8_width(characters[pos - 1]);
            
            let need_new_chunk = current_chunk_payload == 0 || current_chunk_payload + char_width > c;
            
            let wire_needed = if need_new_chunk {
                h.checked_add(char_width).unwrap_or(u64::MAX)
            } else {
                char_width
            };
            
            if total_wire.checked_add(wire_needed).unwrap_or(u64::MAX) > b {
                cause = "LIMIT";
                break;
            }
            
            if need_new_chunk {
                chunk_count += 1;
                total_wire += h;
            }
            
            current_chunk_payload += char_width;
            last_chunk_payload = current_chunk_payload;
            total_payload += char_width;
            total_wire += char_width;
            last_pos = pos;
            
            if segment_ends.iter().any(|&end| pos == end) {
                current_chunk_payload = 0;
            }
        }
        
        let characters_sent = if last_pos > 0 { last_pos - l + 1 } else { 0 };
        
        println!("{} {} {} {} {} {} {}", 
            total_payload, total_wire, characters_sent, last_pos, chunk_count, last_chunk_payload, cause);
    }
}