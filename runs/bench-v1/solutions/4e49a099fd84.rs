use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s = lines.next().unwrap().unwrap();
    let q: usize = lines.next().unwrap().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let n = scalars.len();
    
    if n == 0 {
        for _ in 0..q {
            lines.next();
        }
        return;
    }
    
    let mut grapheme_boundaries = vec![0];
    let mut utf16_pos = 0;
    
    for i in 0..n {
        if i > 0 && has_boundary(&scalars, i) {
            grapheme_boundaries.push(i);
        }
        utf16_pos += utf16_units(scalars[i]);
    }
    grapheme_boundaries.push(n);
    
    let num_graphemes = grapheme_boundaries.len() - 1;
    
    let mut boundary_utf16 = vec![0];
    utf16_pos = 0;
    for i in 0..n {
        if i > 0 && has_boundary(&scalars, i) {
            boundary_utf16.push(utf16_pos);
        }
        utf16_pos += utf16_units(scalars[i]);
    }
    boundary_utf16.push(utf16_pos);
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        let qtype: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let i = resolve(a, num_graphemes as i64) as usize;
        let j = resolve(b, num_graphemes as i64) as usize;
        
        if qtype == 1 {
            if j >= i {
                println!("{} {}", boundary_utf16[i], boundary_utf16[j]);
            } else {
                println!("{} {}", boundary_utf16[i], boundary_utf16[i]);
            }
        } else {
            let mut l = 0;
            while i + l < num_graphemes && j + l < num_graphemes {
                let i_start = grapheme_boundaries[i + l];
                let i_end = grapheme_boundaries[i + l + 1];
                let j_start = grapheme_boundaries[j + l];
                let j_end = grapheme_boundaries[j + l + 1];
                
                if i_end - i_start != j_end - j_start || scalars[i_start..i_end] != scalars[j_start..j_end] {
                    break;
                }
                l += 1;
            }
            
            let units = boundary_utf16[i + l] - boundary_utf16[i];
            println!("{} {}", l, units);
        }
    }
}

fn resolve(idx: i64, g: i64) -> i64 {
    let resolved = if idx >= 0 { idx } else { g + idx };
    resolved.max(0).min(g)
}

fn has_boundary(scalars: &[u32], pos: usize) -> bool {
    if pos == 0 || pos >= scalars.len() {
        return true;
    }
    
    let left = scalars[pos - 1];
    let right = scalars[pos];
    
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
        let mut i = pos - 1;
        while i > 0 {
            i -= 1;
            if !is_attachment(scalars[i]) {
                if is_emoji(scalars[i]) {
                    return false;
                }
                break;
            }
        }
    }
    
    if is_regional_indicator(left) && is_regional_indicator(right) {
        let mut count = 1;
        let mut i = pos - 1;
        while i > 0 && is_regional_indicator(scalars[i - 1]) {
            count += 1;
            i -= 1;
        }
        return count % 2 == 0;
    }
    
    true
}

fn is_control(c: u32) -> bool {
    (c <= 0x001F) || (c >= 0x007F && c <= 0x009F)
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
    (c >= 0x2600 && c <= 0x27BF) || (c >= 0x1F000 && c <= 0x1FAFF)
}

fn is_regional_indicator(c: u32) -> bool {
    c >= 0x1F1E6 && c <= 0x1F1FF
}

fn utf16_units(c: u32) -> usize {
    if c > 0xFFFF { 2 } else { 1 }
}