use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s_line = lines.next().unwrap().unwrap();
    let q: usize = lines.next().unwrap().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s_line.chars().map(|c| c as u32).collect();
    let n = scalars.len();
    
    let mut has_boundary_after = vec![false; n];
    for i in 0..n-1 {
        if compute_boundary(scalars[i], scalars[i+1], &scalars, i) {
            has_boundary_after[i] = true;
        }
    }
    has_boundary_after[n-1] = true;
    
    let mut graphemes = vec![];
    let mut current = vec![];
    for (i, &scalar) in scalars.iter().enumerate() {
        current.push(scalar);
        if has_boundary_after[i] {
            graphemes.push(current);
            current = vec![];
        }
    }
    
    let mut offsets = vec![0u64];
    for &scalar in &scalars {
        let prev = *offsets.last().unwrap();
        let width = if scalar <= 0xFFFF { 1 } else { 2 };
        offsets.push(prev + width);
    }
    
    let mut grapheme_offsets = vec![0u64];
    let mut scalar_idx = 0;
    for grapheme in &graphemes {
        scalar_idx += grapheme.len();
        grapheme_offsets.push(offsets[scalar_idx]);
    }
    
    let num_graphemes = graphemes.len();
    
    for _ in 0..q {
        let query_line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = query_line.split_whitespace().collect();
        let qtype: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let i = resolve_index(a, num_graphemes as i64) as usize;
        let j = resolve_index(b, num_graphemes as i64) as usize;
        
        if qtype == 1 {
            let (i_out, j_out) = if j >= i { (i, j) } else { (i, i) };
            println!("{} {}", grapheme_offsets[i_out], grapheme_offsets[j_out]);
        } else {
            let mut l = 0;
            while i + l < graphemes.len() && j + l < graphemes.len() && graphemes[i + l] == graphemes[j + l] {
                l += 1;
            }
            let byte_units = grapheme_offsets[i + l] - grapheme_offsets[i];
            println!("{} {}", l, byte_units);
        }
    }
}

fn resolve_index(x: i64, g: i64) -> i64 {
    let resolved = if x >= 0 { x } else { g + x };
    resolved.max(0).min(g)
}

fn is_control(c: u32) -> bool {
    (c <= 0x1F) || (c >= 0x7F && c <= 0x9F)
}

fn is_attachment(c: u32) -> bool {
    (c >= 0x0300 && c <= 0x036F) ||
    (c >= 0x1AB0 && c <= 0x1AFF) ||
    (c >= 0x1DC0 && c <= 0x1DFF) ||
    (c >= 0x20D0 && c <= 0x20FF) ||
    (c >= 0xFE00 && c <= 0xFE0F) ||
    (c >= 0xFE20 && c <= 0xFE2F) ||
    (c >= 0x1F3FB && c <= 0x1F3FF) ||
    (c >= 0xE0100 && c <= 0xE01EF)
}

fn is_emoji(c: u32) -> bool {
    (c >= 0x2600 && c <= 0x27BF) ||
    (c >= 0x1F000 && c <= 0x1FAFF)
}

fn is_regional_indicator(c: u32) -> bool {
    c >= 0x1F1E6 && c <= 0x1F1FF
}

fn compute_boundary(left: u32, right: u32, scalars: &[u32], pos: usize) -> bool {
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
        let mut check_idx = pos;
        while check_idx > 0 && is_attachment(scalars[check_idx - 1]) {
            check_idx -= 1;
        }
        if check_idx > 0 && is_emoji(scalars[check_idx - 1]) {
            return false;
        }
    }
    
    if is_regional_indicator(left) && is_regional_indicator(right) {
        let mut count = 1;
        let mut idx = pos;
        while idx > 0 && is_regional_indicator(scalars[idx - 1]) {
            count += 1;
            idx -= 1;
        }
        return count % 2 == 0;
    }
    
    true
}