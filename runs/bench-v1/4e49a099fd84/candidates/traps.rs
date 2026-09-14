fn main() {
    use std::io::{self, BufRead};
    
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s_line = lines.next().unwrap().unwrap();
    let q_line = lines.next().unwrap().unwrap();
    let q: usize = q_line.parse().unwrap();
    
    let scalars: Vec<u32> = s_line.chars().map(|c| c as u32).collect();
    
    let mut is_boundary = vec![true];
    for i in 0..scalars.len() - 1 {
        let left = scalars[i];
        let right = scalars[i + 1];
        is_boundary.push(has_boundary(left, right, &scalars, i));
    }
    
    let mut grapheme_starts = vec![0];
    for i in 1..scalars.len() {
        if is_boundary[i] {
            grapheme_starts.push(i);
        }
    }
    grapheme_starts.push(scalars.len());
    
    let num_graphemes = grapheme_starts.len() - 1;
    
    let mut utf16_offsets = vec![0];
    let mut utf16_pos = 0i64;
    let mut next_start_idx = 1;
    
    for i in 0..scalars.len() {
        utf16_pos += if scalars[i] > 0xFFFF { 2 } else { 1 };
        if next_start_idx < grapheme_starts.len() && i + 1 == grapheme_starts[next_start_idx] {
            utf16_offsets.push(utf16_pos);
            next_start_idx += 1;
        }
    }
    
    let g = num_graphemes as i64;
    
    for _ in 0..q {
        let query_line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = query_line.split_whitespace().collect();
        let query_type: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let resolve = |x: i64| -> i64 {
            let pos = if x >= 0 { x } else { g + x };
            pos.max(0).min(g)
        };
        
        let i = resolve(a) as usize;
        let j = resolve(b) as usize;
        
        if query_type == 1 {
            if j >= i {
                println!("{} {}", utf16_offsets[i], utf16_offsets[j]);
            } else {
                println!("{} {}", utf16_offsets[i], utf16_offsets[i]);
            }
        } else {
            let mut l = 0;
            while i + l < num_graphemes && j + l < num_graphemes {
                let s1 = grapheme_starts[i + l];
                let e1 = grapheme_starts[i + l + 1];
                let s2 = grapheme_starts[j + l];
                let e2 = grapheme_starts[j + l + 1];
                
                if e1 - s1 != e2 - s2 {
                    break;
                }
                
                let mut equal = true;
                for k in 0..(e1 - s1) {
                    if scalars[s1 + k] != scalars[s2 + k] {
                        equal = false;
                        break;
                    }
                }
                
                if !equal {
                    break;
                }
                l += 1;
            }
            println!("{} {}", l, utf16_offsets[i + l] - utf16_offsets[i]);
        }
    }
}

fn has_boundary(left: u32, right: u32, scalars: &[u32], i: usize) -> bool {
    let is_control = |c: u32| (c <= 0x1F) || (c >= 0x7F && c <= 0x9F);
    let is_attachment = |c: u32| {
        (c >= 0x300 && c <= 0x36F) || (c >= 0x1AB0 && c <= 0x1AFF) ||
        (c >= 0x1DC0 && c <= 0x1DFF) || (c >= 0x20D0 && c <= 0x20FF) ||
        (c >= 0xFE00 && c <= 0xFE0F) || (c >= 0xFE20 && c <= 0xFE2F) ||
        (c >= 0x1F3FB && c <= 0x1F3FF) || (c >= 0xE0100 && c <= 0xE01EF)
    };
    let is_emoji = |c: u32| (c >= 0x2600 && c <= 0x27BF) || (c >= 0x1F000 && c <= 0x1FAFF);
    let is_regional = |c: u32| c >= 0x1F1E6 && c <= 0x1F1FF;
    
    if left == 0xD && right == 0xA { return false; }
    if is_control(left) || is_control(right) { return true; }
    if is_attachment(right) || right == 0x200D { return false; }
    if left == 0x200D && is_emoji(right) {
        for j in (0..i).rev() {
            if !is_attachment(scalars[j]) {
                return !is_emoji(scalars[j]);
            }
        }
        return true;
    }
    if is_regional(left) && is_regional(right) {
        let mut count = 1;
        for j in (0..i).rev() {
            if is_regional(scalars[j]) { count += 1; }
            else { break; }
        }
        return count % 2 == 0;
    }
    true
}