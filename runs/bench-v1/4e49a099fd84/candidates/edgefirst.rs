use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s_line = lines.next().unwrap().unwrap();
    let q_line = lines.next().unwrap().unwrap();
    let q: usize = q_line.parse().unwrap();
    
    let scalars: Vec<u32> = s_line.chars().map(|c| c as u32).collect();
    let n = scalars.len();
    
    if n == 0 {
        for _ in 0..q {
            let _ = lines.next().unwrap().unwrap();
            println!("0 0");
        }
        return;
    }
    
    let mut utf16_lengths = Vec::new();
    for &scalar in &scalars {
        let len = if scalar <= 0xFFFF { 1 } else { 2 };
        utf16_lengths.push(len);
    }
    
    let mut has_boundary_after = vec![false; n - 1];
    for i in 0..n - 1 {
        if is_grapheme_boundary(scalars[i], scalars[i + 1], &scalars, i) {
            has_boundary_after[i] = true;
        }
    }
    
    let mut boundaries = vec![0];
    for i in 0..n - 1 {
        if has_boundary_after[i] {
            boundaries.push(i + 1);
        }
    }
    boundaries.push(n);
    
    let num_graphemes = boundaries.len() - 1;
    
    let mut utf16_at_scalar = vec![0];
    let mut offset = 0;
    for i in 0..n {
        offset += utf16_lengths[i];
        utf16_at_scalar.push(offset);
    }
    
    let mut utf16_at_boundary = Vec::new();
    for &boundary in &boundaries {
        utf16_at_boundary.push(utf16_at_scalar[boundary]);
    }
    
    for _ in 0..q {
        let query_line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = query_line.split_whitespace().collect();
        let qtype: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let i = resolve_index(a, num_graphemes);
        let j = resolve_index(b, num_graphemes);
        
        match qtype {
            1 => {
                let (ii, jj) = if j >= i { (i, j) } else { (i, i) };
                println!("{} {}", utf16_at_boundary[ii], utf16_at_boundary[jj]);
            }
            2 => {
                let mut l = 0;
                while i + l < num_graphemes && j + l < num_graphemes {
                    let gi_start = boundaries[i + l];
                    let gi_end = boundaries[i + l + 1];
                    let gj_start = boundaries[j + l];
                    let gj_end = boundaries[j + l + 1];
                    
                    if gi_end - gi_start != gj_end - gj_start {
                        break;
                    }
                    
                    let mut same = true;
                    for k in 0..(gi_end - gi_start) {
                        if scalars[gi_start + k] != scalars[gj_start + k] {
                            same = false;
                            break;
                        }
                    }
                    
                    if !same {
                        break;
                    }
                    
                    l += 1;
                }
                
                let utf16_count = if l == 0 {
                    0
                } else {
                    utf16_at_boundary[i + l] - utf16_at_boundary[i]
                };
                
                println!("{} {}", l, utf16_count);
            }
            _ => {}
        }
    }
}

fn resolve_index(x: i64, g: usize) -> usize {
    let g_i64 = g as i64;
    let resolved = if x < 0 { g_i64 + x } else { x };
    (resolved.max(0).min(g_i64)) as usize
}

fn is_grapheme_boundary(left: u32, right: u32, scalars: &[u32], left_idx: usize) -> bool {
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
        let mut idx = left_idx;
        while idx > 0 && is_attachment(scalars[idx - 1]) {
            idx -= 1;
        }
        if idx > 0 && is_emoji(scalars[idx - 1]) {
            return false;
        }
    }
    
    if is_regional_indicator(left) && is_regional_indicator(right) {
        let mut count = 1;
        let mut idx = left_idx;
        while idx > 0 && is_regional_indicator(scalars[idx - 1]) {
            count += 1;
            idx -= 1;
        }
        if count % 2 == 1 {
            return false;
        }
    }
    
    true
}

fn is_control(scalar: u32) -> bool {
    (scalar >= 0x0000 && scalar <= 0x001F) || (scalar >= 0x007F && scalar <= 0x009F)
}

fn is_attachment(scalar: u32) -> bool {
    (scalar >= 0x0300 && scalar <= 0x036F)
        || (scalar >= 0x1AB0 && scalar <= 0x1AFF)
        || (scalar >= 0x1DC0 && scalar <= 0x1DFF)
        || (scalar >= 0x20D0 && scalar <= 0x20FF)
        || (scalar >= 0xFE00 && scalar <= 0xFE0F)
        || (scalar >= 0xFE20 && scalar <= 0xFE2F)
        || (scalar >= 0x1F3FB && scalar <= 0x1F3FF)
        || (scalar >= 0xE0100 && scalar <= 0xE01EF)
}

fn is_emoji(scalar: u32) -> bool {
    (scalar >= 0x2600 && scalar <= 0x27BF) || (scalar >= 0x1F000 && scalar <= 0x1FAFF)
}

fn is_regional_indicator(scalar: u32) -> bool {
    scalar >= 0x1F1E6 && scalar <= 0x1F1FF
}