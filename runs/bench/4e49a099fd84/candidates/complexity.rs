use std::io::{self, BufRead};

fn compute_boundaries(scalars: &[u32]) -> Vec<usize> {
    let mut boundaries = vec![0];
    for i in 1..scalars.len() {
        if is_grapheme_boundary(scalars, i) {
            boundaries.push(i);
        }
    }
    boundaries.push(scalars.len());
    boundaries
}

fn is_grapheme_boundary(scalars: &[u32], i: usize) -> bool {
    let left = scalars[i - 1];
    let right = scalars[i];
    
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
        for j in (0..i-1).rev() {
            if !is_attachment(scalars[j]) {
                return !is_emoji(scalars[j]);
            }
        }
        return true;
    }
    
    if is_regional_indicator(left) && is_regional_indicator(right) {
        let mut count = 1;
        for j in (0..i-1).rev() {
            if is_regional_indicator(scalars[j]) {
                count += 1;
            } else {
                break;
            }
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

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s = lines.next().unwrap().unwrap();
    let q = lines.next().unwrap().unwrap().parse::<usize>().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let boundaries = compute_boundaries(&scalars);
    
    let mut utf16_at_scalar = vec![0];
    for &scalar in &scalars {
        let offset = if scalar > 0xFFFF { 2 } else { 1 };
        utf16_at_scalar.push(utf16_at_scalar.last().unwrap() + offset);
    }
    
    let num_graphemes = (boundaries.len() - 1) as i64;
    
    for _ in 0..q {
        let query = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = query.split_whitespace().collect();
        let query_type = parts[0].parse::<u32>().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let i = if a >= 0 { (a.min(num_graphemes)) as usize } else { ((num_graphemes + a).max(0)) as usize };
        let j = if b >= 0 { (b.min(num_graphemes)) as usize } else { ((num_graphemes + b).max(0)) as usize };
        
        if query_type == 1 {
            let (start_boundary, end_boundary) = if j >= i { (boundaries[i], boundaries[j]) } else { (boundaries[i], boundaries[i]) };
            println!("{} {}", utf16_at_scalar[start_boundary], utf16_at_scalar[end_boundary]);
        } else {
            let max_len = ((boundaries.len() - 1 - i).min(boundaries.len() - 1 - j)) as i64;
            let mut l = 0;
            for k in 0..max_len {
                let k_usize = k as usize;
                let start1 = boundaries[i + k_usize];
                let end1 = boundaries[i + k_usize + 1];
                let start2 = boundaries[j + k_usize];
                let end2 = boundaries[j + k_usize + 1];
                
                if end1 - start1 != end2 - start2 || scalars[start1..end1] != scalars[start2..end2] {
                    break;
                }
                l = k + 1;
            }
            let start_utf16 = utf16_at_scalar[boundaries[i]];
            let end_utf16 = utf16_at_scalar[boundaries[i + l as usize]];
            println!("{} {}", l, end_utf16 - start_utf16);
        }
    }
}