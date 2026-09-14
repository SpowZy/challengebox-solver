fn main() {
    let mut input = String::new();
    std::io::Read::read_to_string(&mut std::io::stdin(), &mut input).unwrap();
    let mut tokens = input.split_whitespace();
    
    let n: usize = tokens.next().unwrap().parse().unwrap();
    let s: usize = tokens.next().unwrap().parse().unwrap();
    let q: usize = tokens.next().unwrap().parse().unwrap();
    let c: u64 = tokens.next().unwrap().parse().unwrap();
    let h: u64 = tokens.next().unwrap().parse().unwrap();
    
    let mut char_sizes = Vec::new();
    for _ in 0..n {
        let hex = tokens.next().unwrap();
        let codepoint: u32 = u32::from_str_radix(hex, 16).unwrap();
        let size = if codepoint <= 0x7F { 1u64 } else if codepoint <= 0x7FF { 2 } else if codepoint <= 0xFFFF { 3 } else { 4 };
        char_sizes.push(size);
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
        
        let mut payload_bytes = 0u64;
        let mut wire_bytes = 0u64;
        let mut characters = 0usize;
        let mut last = 0usize;
        let mut chunks = 0usize;
        let mut last_chunk_payload = 0u64;
        let mut cause = "END";
        
        let mut current_chunk_payload = 0u64;
        
        for i in l..=r {
            let char_size = char_sizes[i - 1];
            let starting_new_chunk = current_chunk_payload == 0 || current_chunk_payload + char_size > c;
            let bytes_needed = if starting_new_chunk { h + char_size } else { char_size };
            
            if wire_bytes + bytes_needed > b {
                cause = "LIMIT";
                break;
            }
            
            if starting_new_chunk {
                wire_bytes += h;
                current_chunk_payload = 0;
            }
            
            payload_bytes += char_size;
            wire_bytes += char_size;
            current_chunk_payload += char_size;
            characters += 1;
            last = i;
            
            if segment_ends.contains(&i) {
                chunks += 1;
                last_chunk_payload = current_chunk_payload;
                current_chunk_payload = 0;
            } else {
                last_chunk_payload = current_chunk_payload;
            }
        }
        
        if current_chunk_payload > 0 {
            chunks += 1;
            last_chunk_payload = current_chunk_payload;
        }
        
        println!("{} {} {} {} {} {} {}", 
            payload_bytes, wire_bytes, characters, last, chunks, last_chunk_payload, cause);
    }
}