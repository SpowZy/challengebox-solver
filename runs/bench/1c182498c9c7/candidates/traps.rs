use std::io::Read;

fn utf8_width(scalar: u32) -> u64 {
    if scalar <= 0x7F {
        1
    } else if scalar <= 0x7FF {
        2
    } else if scalar <= 0xFFFF {
        3
    } else {
        4
    }
}

fn main() {
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).unwrap();
    
    let mut lines = input.lines();
    
    let header: Vec<&str> = lines.next().unwrap().split_whitespace().collect();
    let n: usize = header[0].parse().unwrap();
    let s: usize = header[1].parse().unwrap();
    let q: usize = header[2].parse().unwrap();
    let c: u64 = header[3].parse().unwrap();
    let h: u64 = header[4].parse().unwrap();
    
    let mut all_tokens = Vec::new();
    while all_tokens.len() < n {
        if let Some(line) = lines.next() {
            all_tokens.extend(line.split_whitespace().collect::<Vec<_>>());
        } else {
            break;
        }
    }
    
    let char_vec: Vec<u32> = all_tokens.iter().take(n)
        .map(|t| u32::from_str_radix(t, 16).unwrap())
        .collect();
    
    let mut all_tokens = Vec::new();
    while all_tokens.len() < s {
        if let Some(line) = lines.next() {
            all_tokens.extend(line.split_whitespace().collect::<Vec<_>>());
        } else {
            break;
        }
    }
    
    let seg_vec: Vec<usize> = all_tokens.iter().take(s)
        .map(|t| t.parse().unwrap())
        .collect();
    
    let widths: Vec<u64> = char_vec.iter().map(|&c| utf8_width(c)).collect();
    
    let mut is_seg_boundary = vec![false; n];
    let mut pos = 0;
    for i in 0..s.saturating_sub(1) {
        pos += seg_vec[i];
        if pos < n {
            is_seg_boundary[pos] = true;
        }
    }
    
    for _ in 0..q {
        let line = lines.next().unwrap();
        let req: Vec<&str> = line.split_whitespace().collect();
        let l: usize = req[0].parse::<usize>().unwrap() - 1;
        let r: usize = req[1].parse::<usize>().unwrap() - 1;
        let b: u128 = req[2].parse::<u128>().unwrap();
        
        let mut payload: u128 = 0;
        let mut wire: u128 = 0;
        let mut count = 0u64;
        let mut last = 0usize;
        let mut chunks = 0u64;
        let mut last_chunk_size: u128 = 0;
        let mut cause = "END";
        
        let mut chunk_size: u128 = 0;
        let h_val = h as u128;
        let c_val = c as u128;
        
        for pos in l..=r {
            let is_boundary = is_seg_boundary[pos];
            let new_chunk = chunk_size == 0 || is_boundary;
            
            let w = widths[pos] as u128;
            
            if new_chunk {
                if wire + h_val + w > b {
                    cause = "LIMIT";
                    break;
                }
                wire += h_val;
                chunks += 1;
                chunk_size = 0;
            } else {
                if wire + w > b {
                    cause = "LIMIT";
                    break;
                }
            }
            
            if chunk_size + w > c_val {
                cause = "LIMIT";
                break;
            }
            
            payload += w;
            wire += w;
            count += 1;
            last = pos + 1;
            chunk_size += w;
            last_chunk_size = chunk_size;
        }
        
        println!("{} {} {} {} {} {} {}", payload, wire, count, last, chunks, last_chunk_size, cause);
    }
}