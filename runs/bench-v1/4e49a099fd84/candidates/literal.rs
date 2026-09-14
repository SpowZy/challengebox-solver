fn main() {
    use std::io::{self, BufRead};
    
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s = lines.next().unwrap().unwrap();
    let q: usize = lines.next().unwrap().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let n = scalars.len();
    
    let mut boundaries = vec![0];
    for i in 1..n {
        if has_boundary(&scalars, i) {
            boundaries.push(i);
        }
    }
    boundaries.push(n);
    
    for _ in 0..q {
        let query_line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = query_line.split_whitespace().collect();
        let query_type: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let num_graphemes = (boundaries.len() - 1) as u64;
        let i = resolve_index(a, num_graphemes) as usize;
        let j = resolve_index(b, num_graphemes) as usize;
        
        if query_type == 1 {
            let (first_idx, second_idx) = if j >= i { (i, j) } else { (i, i) };
            let first_offset = to_utf16_offset(&scalars, boundaries[first_idx]);
            let second_offset = to_utf16_offset(&scalars, boundaries[second_idx]);
            println!("{} {}", first_offset, second_offset);
        } else {
            let (l, code_units) = find_common_length(i, j, &boundaries, &scalars);
            println!("{} {}", l, code_units);
        }
    }
}

fn resolve_index(x: i64, g: u64) -> i64 {
    let resolved = if x >= 0 { x } else { (g as i64) + x };
    resolved.max(0).min(g as i64)
}

fn has_boundary(scalars: &[u32], pos: usize) -> bool {
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
        for k in (0..pos - 1).rev() {
            if !is_attachment(scalars[k]) {
                if is_emoji(scalars[k]) {
                    return false;
                }
                break;
            }
        }
    }
    
    if is_regional_indicator(left) && is_regional_indicator(right) {
        let mut count = 1;
        let mut k = pos - 1;
        while k > 0 && is_regional_indicator(scalars[k - 1]) {
            count += 1;
            k -= 1;
        }
        if count % 2 == 1 {
            return false;
        }
    }
    
    true
}

fn is_control(scalar: u32) -> bool {
    scalar <= 0x001F || (scalar >= 0x007F && scalar <= 0x009F)
}

fn is_attachment(scalar: u32) -> bool {
    matches!(scalar,
        0x0300..=0x036F | 0x1AB0..=0x1AFF | 0x1DC0..=0x1DFF | 0x20D0..=0x20FF |
        0xFE00..=0xFE0F | 0xFE20..=0xFE2F | 0x1F3FB..=0x1F3FF | 0xE0100..=0xE01EF
    )
}

fn is_emoji(scalar: u32) -> bool {
    matches!(scalar, 0x2600..=0x27BF | 0x1F000..=0x1FAFF)
}

fn is_regional_indicator(scalar: u32) -> bool {
    matches!(scalar, 0x1F1E6..=0x1F1FF)
}

fn to_utf16_offset(scalars: &[u32], pos: usize) -> u64 {
    let mut offset = 0u64;
    for i in 0..pos {
        offset += if scalars[i] <= 0xFFFF { 1 } else { 2 };
    }
    offset
}

fn find_common_length(i: usize, j: usize, boundaries: &[usize], scalars: &[u32]) -> (u64, u64) {
    let g = boundaries.len() - 1;
    let mut length = 0u64;
    
    while (i as u64) + length < (g as u64) && (j as u64) + length < (g as u64) {
        let start_i = boundaries[i + length as usize];
        let end_i = boundaries[i + (length as usize) + 1];
        let start_j = boundaries[j + length as usize];
        let end_j = boundaries[j + (length as usize) + 1];
        
        if end_i - start_i != end_j - start_j {
            break;
        }
        
        let mut same = true;
        for k in 0..(end_i - start_i) {
            if scalars[start_i + k] != scalars[start_j + k] {
                same = false;
                break;
            }
        }
        
        if !same {
            break;
        }
        
        length += 1;
    }
    
    let code_units = to_utf16_offset(scalars, boundaries[i + length as usize]) -
                     to_utf16_offset(scalars, boundaries[i]);
    
    (length, code_units)
}