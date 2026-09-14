use std::io;

fn utf8_width(codepoint: u32) -> u64 {
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

fn main() {
    let stdin = io::stdin();
    let mut line = String::new();
    
    line.clear();
    stdin.read_line(&mut line).unwrap();
    let parts: Vec<&str> = line.split_whitespace().collect();
    let _n: usize = parts[0].parse().unwrap();
    let _s: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    let c: u64 = parts[3].parse().unwrap();
    let h: u64 = parts[4].parse().unwrap();
    
    line.clear();
    stdin.read_line(&mut line).unwrap();
    let char_strs: Vec<&str> = line.split_whitespace().collect();
    let chars: Vec<u32> = char_strs.iter().map(|s| u32::from_str_radix(s, 16).unwrap()).collect();
    
    line.clear();
    stdin.read_line(&mut line).unwrap();
    let seg_strs: Vec<&str> = line.split_whitespace().collect();
    let mut seg_end = vec![];
    let mut pos = 0;
    for seg_str in &seg_strs {
        let len: usize = seg_str.parse().unwrap();
        pos += len;
        seg_end.push(pos);
    }
    
    let get_segment = |idx: usize| -> usize {
        for (i, &end) in seg_end.iter().enumerate() {
            if idx < end {
                return i;
            }
        }
        seg_end.len() - 1
    };
    
    for _ in 0..q {
        line.clear();
        stdin.read_line(&mut line).unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let l_orig: usize = parts[0].parse::<usize>().unwrap();
        let r_orig: usize = parts[1].parse::<usize>().unwrap();
        let b: u64 = parts[2].parse().unwrap();
        let l: usize = l_orig - 1;
        let r: usize = r_orig - 1;
        
        let mut payload_bytes: u64 = 0;
        let mut wire_bytes: u64 = 0;
        let mut last: usize = 0;
        let mut chunks: u64 = 0;
        let mut last_chunk_payload: u64 = 0;
        let mut cause = "LIMIT";
        
        let mut current_chunk_payload: u64 = 0;
        let mut current_segment = get_segment(l);
        
        for pos in l..=r {
            let char_width = utf8_width(chars[pos]);
            let char_segment = get_segment(pos);
            
            let need_new_chunk = current_chunk_payload == 0 ||
                                current_chunk_payload + char_width > c ||
                                char_segment != current_segment;
            
            let total_additional = if need_new_chunk { h.saturating_add(char_width) } else { char_width };
            let new_wire = wire_bytes.saturating_add(total_additional);
            
            if new_wire > b {
                cause = if pos == r { "END" } else { "LIMIT" };
                break;
            }
            
            if need_new_chunk {
                chunks = chunks.saturating_add(1);
                wire_bytes = wire_bytes.saturating_add(h);
                current_chunk_payload = 0;
                current_segment = char_segment;
            }
            
            payload_bytes = payload_bytes.saturating_add(char_width);
            wire_bytes = wire_bytes.saturating_add(char_width);
            current_chunk_payload = current_chunk_payload.saturating_add(char_width);
            last = pos + 1;
            last_chunk_payload = current_chunk_payload;
            
            if pos == r {
                cause = "END";
            }
        }
        
        let characters = if last > 0 { last - l_orig + 1 } else { 0 };
        println!("{} {} {} {} {} {} {}", payload_bytes, wire_bytes, characters, last, chunks, last_chunk_payload, cause);
    }
}