use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s = lines.next().unwrap().unwrap();
    let q: usize = lines.next().unwrap().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let boundaries = compute_boundaries(&scalars);
    let num_graphemes = boundaries.len() - 1;
    let utf16_offsets = compute_utf16_offsets(&scalars, &boundaries);
    
    for _ in 0..q {
        let query_line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = query_line.split_whitespace().collect();
        let query_type: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let i = resolve_index(a, num_graphemes);
        let j = resolve_index(b, num_graphemes);
        
        if query_type == 1 {
            if j >= i {
                println!("{} {}", utf16_offsets[i], utf16_offsets[j]);
            } else {
                println!("{} {}", utf16_offsets[i], utf16_offsets[i]);
            }
        } else {
            let (l, units) = find_longest_match(&scalars, &boundaries, &utf16_offsets, i, j);
            println!("{} {}", l, units);
        }
    }
}

fn is_attachment(s: u32) -> bool {
    (s >= 0x0300 && s <= 0x036F) || (s >= 0x1AB0 && s <= 0x1AFF) ||
    (s >= 0x1DC0 && s <= 0x1DFF) || (s >= 0x20D0 && s <= 0x20FF) ||
    (s >= 0xFE00 && s <= 0xFE0F) || (s >= 0xFE20 && s <= 0xFE2F) ||
    (s >= 0x1F3FB && s <= 0x1F3FF) || (s >= 0xE0100 && s <= 0xE01EF)
}

fn is_emoji(s: u32) -> bool {
    (s >= 0x2600 && s <= 0x27BF) || (s >= 0x1F000 && s <= 0x1FAFF)
}

fn is_regional_indicator(s: u32) -> bool {
    s >= 0x1F1E6 && s <= 0x1F1FF
}

fn is_control(s: u32) -> bool {
    (s >= 0x0000 && s <= 0x001F) || (s >= 0x007F && s <= 0x009F)
}

fn check_boundary(left: u32, right: u32, scalars: &[u32], left_idx: usize) -> bool {
    if left == 0x000D && right == 0x000A {
        return false;
    }
    
    if is_control(left) || is_control(right) {
        return true;
    }
    
    if is_attachment(right) || right == 0x200D {
        return false;
    }
    
    if left == 0x200D {
        if is_emoji(right) {
            let mut j = left_idx as i32 - 1;
            while j >= 0 && is_attachment(scalars[j as usize]) {
                j -= 1;
            }
            if j >= 0 && is_emoji(scalars[j as usize]) {
                return false;
            }
        }
        return true;
    }
    
    if is_regional_indicator(left) && is_regional_indicator(right) {
        let mut count = 1;
        let mut k = left_idx as i32 - 1;
        while k >= 0 && is_regional_indicator(scalars[k as usize]) {
            count += 1;
            k -= 1;
        }
        return count % 2 == 0;
    }
    
    true
}

fn compute_boundaries(scalars: &[u32]) -> Vec<usize> {
    let mut boundaries = vec![0];
    for i in 0..scalars.len() - 1 {
        if check_boundary(scalars[i], scalars[i + 1], scalars, i) {
            boundaries.push(i + 1);
        }
    }
    boundaries.push(scalars.len());
    boundaries
}

fn compute_utf16_offsets(scalars: &[u32], boundaries: &[usize]) -> Vec<usize> {
    let mut offsets = Vec::new();
    let mut utf16_pos = 0;
    let mut scalar_idx = 0;
    
    for &boundary in boundaries {
        while scalar_idx < boundary {
            utf16_pos += if scalars[scalar_idx] <= 0xFFFF { 1 } else { 2 };
            scalar_idx += 1;
        }
        offsets.push(utf16_pos);
    }
    
    offsets
}

fn resolve_index(x: i64, g: usize) -> usize {
    let resolved = if x >= 0 { x } else { g as i64 + x };
    resolved.max(0).min(g as i64) as usize
}

fn find_longest_match(scalars: &[u32], boundaries: &[usize], utf16_offsets: &[usize], i: usize, j: usize) -> (usize, usize) {
    let g = boundaries.len() - 1;
    let mut l = 0;
    
    while i + l < g && j + l < g {
        let (si, ei) = (boundaries[i + l], boundaries[i + l + 1]);
        let (sj, ej) = (boundaries[j + l], boundaries[j + l + 1]);
        
        if ei - si == ej - sj && scalars[si..ei] == scalars[sj..ej] {
            l += 1;
        } else {
            break;
        }
    }
    
    (l, utf16_offsets[i + l] - utf16_offsets[i])
}