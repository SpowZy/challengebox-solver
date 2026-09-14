use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s = lines.next().unwrap().unwrap();
    let q_count: usize = lines.next().unwrap().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let n = scalars.len();
    
    let mut is_boundary = vec![true];
    for i in 0..n - 1 {
        is_boundary.push(check_boundary(&scalars, i));
    }
    
    let g = is_boundary.iter().take(n).filter(|&&b| b).count();
    
    let mut byte_offsets = vec![0];
    let mut char_byte_offset = 0;
    for (idx, c) in s.chars().enumerate() {
        char_byte_offset += c.len_utf8();
        if idx + 1 < n && is_boundary[idx + 1] {
            byte_offsets.push(char_byte_offset);
        }
    }
    byte_offsets.push(s.len());
    
    let utf16_offsets: Vec<usize> = byte_offsets.iter()
        .map(|&off| byte_to_utf16(&s, off))
        .collect();
    
    for _ in 0..q_count {
        let query = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = query.split_whitespace().collect();
        let query_type: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let i = resolve_index(a, g as i64) as usize;
        let j = resolve_index(b, g as i64) as usize;
        
        if query_type == 1 {
            if j >= i {
                println!("{} {}", utf16_offsets[i], utf16_offsets[j]);
            } else {
                println!("{} {}", utf16_offsets[i], utf16_offsets[i]);
            }
        } else {
            let mut l = 0;
            while i + l < g && j + l < g {
                let si = byte_offsets[i + l];
                let ei = byte_offsets[i + l + 1];
                let sj = byte_offsets[j + l];
                let ej = byte_offsets[j + l + 1];
                
                if s.as_bytes()[si..ei] != s.as_bytes()[sj..ej] {
                    break;
                }
                l += 1;
            }
            
            let utf16_units = utf16_offsets[i + l] - utf16_offsets[i];
            println!("{} {}", l, utf16_units);
        }
    }
}

fn check_boundary(scalars: &[u32], left_idx: usize) -> bool {
    let left = scalars[left_idx];
    let right = scalars[left_idx + 1];
    
    if left == 0x000D && right == 0x000A {
        return false;
    }
    
    if is_control(left) || is_control(right) {
        return true;
    }
    
    if is_attachment(right) || right == 0x200D {
        return false;
    }
    
    if left == 0x200D && is_emoji(right) {
        let mut idx = left_idx as i32 - 1;
        while idx >= 0 {
            if !is_attachment(scalars[idx as usize]) {
                if is_emoji(scalars[idx as usize]) {
                    return false;
                }
                break;
            }
            idx -= 1;
        }
    }
    
    if is_regional_indicator(left) && is_regional_indicator(right) {
        let mut count = 1;
        let mut idx = left_idx as i32 - 1;
        while idx >= 0 && is_regional_indicator(scalars[idx as usize]) {
            count += 1;
            idx -= 1;
        }
        if count % 2 == 1 {
            return false;
        }
    }
    
    true
}

fn resolve_index(x: i64, g: i64) -> i64 {
    if x < 0 { (g + x).max(0) } else { x.min(g) }
}

fn is_control(s: u32) -> bool {
    (s <= 0x1F) || (s >= 0x7F && s <= 0x9F)
}

fn is_attachment(s: u32) -> bool {
    (s >= 0x0300 && s <= 0x036F) ||
    (s >= 0x1AB0 && s <= 0x1AFF) ||
    (s >= 0x1DC0 && s <= 0x1DFF) ||
    (s >= 0x20D0 && s <= 0x20FF) ||
    (s >= 0xFE00 && s <= 0xFE0F) ||
    (s >= 0xFE20 && s <= 0xFE2F) ||
    (s >= 0x1F3FB && s <= 0x1F3FF) ||
    (s >= 0xE0100 && s <= 0xE01EF)
}

fn is_emoji(s: u32) -> bool {
    (s >= 0x2600 && s <= 0x27BF) ||
    (s >= 0x1F000 && s <= 0x1FAFF)
}

fn is_regional_indicator(s: u32) -> bool {
    s >= 0x1F1E6 && s <= 0x1F1FF
}

fn byte_to_utf16(s: &str, byte_offset: usize) -> usize {
    let bytes = s.as_bytes();
    let mut utf16_pos = 0;
    let mut pos = 0;
    
    while pos < byte_offset {
        let b = bytes[pos];
        if (b & 0x80) == 0 {
            utf16_pos += 1;
            pos += 1;
        } else if (b & 0xE0) == 0xC0 {
            utf16_pos += 1;
            pos += 2;
        } else if (b & 0xF0) == 0xE0 {
            utf16_pos += 1;
            pos += 3;
        } else if (b & 0xF8) == 0xF0 {
            utf16_pos += 2;
            pos += 4;
        } else {
            pos += 1;
        }
    }
    
    utf16_pos
}