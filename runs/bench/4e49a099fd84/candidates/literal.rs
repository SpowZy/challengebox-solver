use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s = lines.next().unwrap().unwrap();
    let q: usize = lines.next().unwrap().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let n = scalars.len();
    
    let boundaries = find_boundaries(&scalars);
    
    let mut utf16_offsets = vec![0u32];
    for &scalar in &scalars {
        let last = *utf16_offsets.last().unwrap();
        let inc = if scalar <= 0xFFFF { 1u32 } else { 2u32 };
        utf16_offsets.push(last + inc);
    }
    
    let mut grapheme_boundaries = Vec::new();
    for i in 0..=n {
        if boundaries[i] {
            grapheme_boundaries.push(i);
        }
    }
    
    let num_graphemes = grapheme_boundaries.len() - 1;
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let qtype: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let g = num_graphemes as i64;
        let mut i = if a >= 0 { a } else { g + a };
        let mut j = if b >= 0 { b } else { g + b };
        
        i = i.max(0).min(g);
        j = j.max(0).min(g);
        
        if qtype == 1 {
            if j < i {
                j = i;
            }
            
            let idx_i = grapheme_boundaries[i as usize];
            let idx_j = grapheme_boundaries[j as usize];
            
            println!("{} {}", utf16_offsets[idx_i], utf16_offsets[idx_j]);
        } else {
            let i = i as usize;
            let j = j as usize;
            
            let mut l = 0;
            while i + l < num_graphemes && j + l < num_graphemes {
                let start1 = grapheme_boundaries[i + l];
                let end1 = grapheme_boundaries[i + l + 1];
                let start2 = grapheme_boundaries[j + l];
                let end2 = grapheme_boundaries[j + l + 1];
                
                if end1 - start1 != end2 - start2 {
                    break;
                }
                
                let mut same = true;
                for k in 0..(end1 - start1) {
                    if scalars[start1 + k] != scalars[start2 + k] {
                        same = false;
                        break;
                    }
                }
                
                if !same {
                    break;
                }
                l += 1;
            }
            
            let start_idx = grapheme_boundaries[i];
            let end_idx = grapheme_boundaries[i + l];
            let utf16_units = utf16_offsets[end_idx] - utf16_offsets[start_idx];
            
            println!("{} {}", l, utf16_units);
        }
    }
}

fn find_boundaries(scalars: &[u32]) -> Vec<bool> {
    let n = scalars.len();
    let mut boundaries = vec![false; n + 1];
    boundaries[0] = true;
    boundaries[n] = true;
    
    for i in 1..n {
        let left = scalars[i - 1];
        let right = scalars[i];
        
        if left == 0x000D && right == 0x000A {
            boundaries[i] = false;
        } else if is_control(left) || is_control(right) {
            boundaries[i] = true;
        } else if is_attachment(right) || right == 0x200D {
            boundaries[i] = false;
        } else if left == 0x200D && is_emoji(right) && has_emoji_before_zerowidth(scalars, i - 1) {
            boundaries[i] = false;
        } else if is_regional_indicator(left) && is_regional_indicator(right) {
            let mut count = 1;
            let mut j = i - 1;
            loop {
                if j == 0 || !is_regional_indicator(scalars[j - 1]) {
                    break;
                }
                j -= 1;
                count += 1;
            }
            boundaries[i] = count % 2 == 0;
        } else {
            boundaries[i] = true;
        }
    }
    
    boundaries
}

fn is_control(c: u32) -> bool {
    (c >= 0x0000 && c <= 0x001F) || (c >= 0x007F && c <= 0x009F)
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

fn has_emoji_before_zerowidth(scalars: &[u32], mut i: usize) -> bool {
    loop {
        if !is_attachment(scalars[i]) {
            return is_emoji(scalars[i]);
        }
        if i == 0 {
            return false;
        }
        i -= 1;
    }
}