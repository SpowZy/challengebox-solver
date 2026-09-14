use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s = lines.next().unwrap().unwrap();
    let q: usize = lines.next().unwrap().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    
    let mut ri_count = vec![0; scalars.len()];
    let mut current_count = 0;
    for i in 0..scalars.len() {
        if is_regional_indicator(scalars[i]) {
            current_count += 1;
        } else {
            current_count = 0;
        }
        ri_count[i] = current_count;
    }
    
    let mut boundaries = vec![true];
    for i in 0..scalars.len() - 1 {
        let is_boundary = check_boundary(scalars[i], scalars[i + 1], &scalars, i, &ri_count);
        boundaries.push(is_boundary);
    }
    
    let mut graphemes = Vec::new();
    let mut current_grapheme = Vec::new();
    for i in 0..scalars.len() {
        if boundaries[i] && !current_grapheme.is_empty() {
            graphemes.push(current_grapheme);
            current_grapheme = Vec::new();
        }
        current_grapheme.push(scalars[i]);
    }
    if !current_grapheme.is_empty() {
        graphemes.push(current_grapheme);
    }
    
    let grapheme_count = graphemes.len() as i64;
    
    let mut grapheme_boundaries = vec![0u64];
    let mut utf16_offset = 0u64;
    for grapheme in &graphemes {
        for &scalar in grapheme {
            utf16_offset += if scalar <= 0xFFFF { 1 } else { 2 };
        }
        grapheme_boundaries.push(utf16_offset);
    }
    
    for _ in 0..q {
        let query = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = query.split_whitespace().collect();
        let query_type: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let i = if a >= 0 { a } else { grapheme_count + a }.max(0).min(grapheme_count);
        let j = if b >= 0 { b } else { grapheme_count + b }.max(0).min(grapheme_count);
        
        match query_type {
            1 => {
                if j >= i {
                    println!("{} {}", grapheme_boundaries[i as usize], grapheme_boundaries[j as usize]);
                } else {
                    println!("{} {}", grapheme_boundaries[i as usize], grapheme_boundaries[i as usize]);
                }
            }
            2 => {
                let mut l = 0i64;
                let max_l = grapheme_count - i.max(j);
                for k in 0..max_l {
                    if graphemes[(i + k) as usize] == graphemes[(j + k) as usize] {
                        l += 1;
                    } else {
                        break;
                    }
                }
                let utf16_units = grapheme_boundaries[(i + l) as usize] - grapheme_boundaries[i as usize];
                println!("{} {}", l, utf16_units);
            }
            _ => {}
        }
    }
}

fn check_boundary(left: u32, right: u32, scalars: &[u32], left_idx: usize, ri_count: &[usize]) -> bool {
    if left == 0x000D && right == 0x000A { return false; }
    if is_control(left) || is_control(right) { return true; }
    if is_attachment(right) || right == 0x200D { return false; }
    if left == 0x200D && is_emoji(right) {
        let mut idx = left_idx;
        while idx > 0 {
            idx -= 1;
            if !is_attachment(scalars[idx]) {
                return !is_emoji(scalars[idx]);
            }
        }
    }
    if is_regional_indicator(left) && is_regional_indicator(right) {
        return ri_count[left_idx] % 2 == 0;
    }
    true
}

fn is_control(c: u32) -> bool {
    (c <= 0x001F) || (c >= 0x007F && c <= 0x009F)
}

fn is_attachment(c: u32) -> bool {
    (c >= 0x0300 && c <= 0x036F) || (c >= 0x1AB0 && c <= 0x1AFF) ||
    (c >= 0x1DC0 && c <= 0x1DFF) || (c >= 0x20D0 && c <= 0x20FF) ||
    (c >= 0xFE00 && c <= 0xFE0F) || (c >= 0xFE20 && c <= 0xFE2F) ||
    (c >= 0x1F3FB && c <= 0x1F3FF) || (c >= 0xE0100 && c <= 0xE01EF)
}

fn is_emoji(c: u32) -> bool {
    (c >= 0x2600 && c <= 0x27BF) || (c >= 0x1F000 && c <= 0x1FAFF)
}

fn is_regional_indicator(c: u32) -> bool {
    c >= 0x1F1E6 && c <= 0x1F1FF
}