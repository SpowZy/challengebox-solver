fn main() {
    use std::io::{self, BufRead};
    
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let s = lines.next().unwrap().unwrap();
    let q: usize = lines.next().unwrap().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let n = scalars.len();
    
    let mut boundaries = vec![0];
    for i in 0..n-1 {
        let left = scalars[i];
        let right = scalars[i+1];
        if has_boundary(left, right, &scalars, i) {
            boundaries.push(i + 1);
        }
    }
    boundaries.push(n);
    
    let g = (boundaries.len() - 1) as i64;
    
    let mut utf16 = vec![0];
    let mut pos = 0;
    for scalar in &scalars {
        pos += if *scalar <= 0xFFFF { 1 } else { 2 };
        utf16.push(pos);
    }
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let ty: u32 = parts[0].parse().unwrap();
        let a: i64 = parts[1].parse().unwrap();
        let b: i64 = parts[2].parse().unwrap();
        
        let i = (if a >= 0 { a } else { g + a }).max(0).min(g) as usize;
        let j = (if b >= 0 { b } else { g + b }).max(0).min(g) as usize;
        
        if ty == 1 {
            if j >= i {
                println!("{} {}", utf16[boundaries[i]], utf16[boundaries[j]]);
            } else {
                println!("{} {}", utf16[boundaries[i]], utf16[boundaries[i]]);
            }
        } else {
            let mut len = 0;
            while i + len < boundaries.len() - 1 && j + len < boundaries.len() - 1 {
                let si = boundaries[i + len];
                let ei = boundaries[i + len + 1];
                let sj = boundaries[j + len];
                let ej = boundaries[j + len + 1];
                
                if ei - si != ej - sj || scalars[si..ei] != scalars[sj..ej] {
                    break;
                }
                len += 1;
            }
            
            let start = boundaries[i];
            let end = boundaries[i + len];
            println!("{} {}", len, utf16[end] - utf16[start]);
        }
    }
}

fn has_boundary(left: u32, right: u32, scalars: &[u32], left_idx: usize) -> bool {
    if left == 0xD && right == 0xA { return false; }
    if (left <= 0x1F || left >= 0x7F && left <= 0x9F) ||
       (right <= 0x1F || right >= 0x7F && right <= 0x9F) { return true; }
    if is_attach(right) || right == 0x200D { return false; }
    
    if left == 0x200D && is_emoji(right) {
        for k in (0..left_idx).rev() {
            if !is_attach(scalars[k]) {
                if is_emoji(scalars[k]) { return false; }
                break;
            }
        }
    }
    
    if is_ri(left) && is_ri(right) {
        let mut cnt = 1;
        for k in (0..left_idx).rev() {
            if is_ri(scalars[k]) { cnt += 1; } else { break; }
        }
        if cnt % 2 == 1 { return false; }
    }
    
    true
}

fn is_attach(c: u32) -> bool {
    (c >= 0x300 && c <= 0x36F) || (c >= 0x1AB0 && c <= 0x1AFF) ||
    (c >= 0x1DC0 && c <= 0x1DFF) || (c >= 0x20D0 && c <= 0x20FF) ||
    (c >= 0xFE00 && c <= 0xFE0F) || (c >= 0xFE20 && c <= 0xFE2F) ||
    (c >= 0x1F3FB && c <= 0x1F3FF) || (c >= 0xE0100 && c <= 0xE01EF)
}

fn is_emoji(c: u32) -> bool {
    (c >= 0x2600 && c <= 0x27BF) || (c >= 0x1F000 && c <= 0x1FAFF)
}

fn is_ri(c: u32) -> bool {
    c >= 0x1F1E6 && c <= 0x1F1FF
}