use std::io::Read;

fn main() {
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).unwrap();
    let mut tokens = input.split_whitespace();
    
    let s = tokens.next().unwrap();
    let q: usize = tokens.next().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let n = scalars.len();
    
    let mut is_boundary = vec![false; n + 1];
    is_boundary[0] = true;
    is_boundary[n] = true;
    
    for i in 1..n {
        if has_boundary(scalars[i-1], scalars[i], &scalars, i-1) {
            is_boundary[i] = true;
        }
    }
    
    let mut grapheme_starts = Vec::new();
    for i in 0..=n {
        if is_boundary[i] {
            grapheme_starts.push(i);
        }
    }
    
    let g = grapheme_starts.len() - 1;
    
    let mut utf16_offset = vec![0; n + 1];
    for i in 0..n {
        utf16_offset[i + 1] = utf16_offset[i] + if scalars[i] <= 0xFFFF { 1 } else { 2 };
    }
    
    for _ in 0..q {
        let query_type: u32 = tokens.next().unwrap().parse().unwrap();
        let a: i64 = tokens.next().unwrap().parse().unwrap();
        let b: i64 = tokens.next().unwrap().parse().unwrap();
        
        let i = resolve_index(a, g as i64) as usize;
        let j = resolve_index(b, g as i64) as usize;
        
        if query_type == 1 {
            let (si, sj) = if j >= i { (i, j) } else { (i, i) };
            println!("{} {}", utf16_offset[grapheme_starts[si]], utf16_offset[grapheme_starts[sj]]);
        } else {
            let mut l = 0;
            while i + l < g && j + l < g {
                let start_i = grapheme_starts[i + l];
                let end_i = grapheme_starts[i + l + 1];
                let start_j = grapheme_starts[j + l];
                let end_j = grapheme_starts[j + l + 1];
                
                if end_i - start_i != end_j - start_j || 
                   scalars[start_i..end_i] != scalars[start_j..end_j] {
                    break;
                }
                l += 1;
            }
            let units = utf16_offset[grapheme_starts[i + l]] - utf16_offset[grapheme_starts[i]];
            println!("{} {}", l, units);
        }
    }
}

fn resolve_index(x: i64, g: i64) -> i64 {
    (if x >= 0 { x } else { g + x }).max(0).min(g)
}

fn has_boundary(left: u32, right: u32, scalars: &[u32], left_idx: usize) -> bool {
    if left == 0x000D && right == 0x000A { return false; }
    if is_control(left) || is_control(right) { return true; }
    if is_attachment(right) || right == 0x200D { return false; }
    
    if left == 0x200D && is_emoji(right) {
        for k in (0..left_idx).rev() {
            if !is_attachment(scalars[k]) {
                return !is_emoji(scalars[k]);
            }
        }
    }
    
    if is_regional_indicator(left) && is_regional_indicator(right) {
        let mut count = 1;
        for k in (0..left_idx).rev() {
            if is_regional_indicator(scalars[k]) {
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
    (c <= 0x1F) || (c >= 0x7F && c <= 0x9F)
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