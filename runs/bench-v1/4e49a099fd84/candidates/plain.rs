use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    
    let mut tokens = input.split_whitespace();
    let s = tokens.next().unwrap();
    let q: usize = tokens.next().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let num_scalars = scalars.len();
    
    let mut is_boundary = vec![true; num_scalars + 1];
    is_boundary[0] = true;
    
    for i in 1..num_scalars {
        is_boundary[i] = has_boundary(&scalars, i);
    }
    is_boundary[num_scalars] = true;
    
    let mut grapheme_to_scalar = Vec::new();
    for i in 0..=num_scalars {
        if is_boundary[i] {
            grapheme_to_scalar.push(i);
        }
    }
    
    let num_graphemes = grapheme_to_scalar.len() - 1;
    
    let mut utf16_offsets = vec![0u64; num_scalars + 1];
    for i in 1..=num_scalars {
        let units = if scalars[i - 1] > 0xFFFF { 2 } else { 1 };
        utf16_offsets[i] = utf16_offsets[i - 1] + units;
    }
    
    for _ in 0..q {
        let qtype: u32 = tokens.next().unwrap().parse().unwrap();
        let a: i64 = tokens.next().unwrap().parse().unwrap();
        let b: i64 = tokens.next().unwrap().parse().unwrap();
        
        let mut i = a;
        let mut j = b;
        let g = num_graphemes as i64;
        
        if i < 0 { i += g; }
        if j < 0 { j += g; }
        i = i.max(0).min(g);
        j = j.max(0).min(g);
        
        if qtype == 1 {
            let i_sc = grapheme_to_scalar[i as usize];
            let j_sc = if j >= i { grapheme_to_scalar[j as usize] } else { i_sc };
            println!("{} {}", utf16_offsets[i_sc], utf16_offsets[j_sc]);
        } else {
            let l = longest_match(&scalars, &grapheme_to_scalar, i as usize, j as usize, num_graphemes);
            let utf16_end = utf16_offsets[grapheme_to_scalar[i as usize + l]];
            let utf16_start = utf16_offsets[grapheme_to_scalar[i as usize]];
            println!("{} {}", l, utf16_end - utf16_start);
        }
    }
}

fn has_boundary(scalars: &[u32], pos: usize) -> bool {
    let left = scalars[pos - 1];
    let right = scalars[pos];
    
    if left == 0x000D && right == 0x000A { return false; }
    
    if is_control(left) || is_control(right) { return true; }
    
    if is_attachment(right) || right == 0x200D { return false; }
    
    if left == 0x200D && is_emoji(right) && pos >= 2 {
        let mut k = pos - 2;
        loop {
            if is_attachment(scalars[k]) {
                if k == 0 { break; }
                k -= 1;
            } else {
                break;
            }
        }
        if is_emoji(scalars[k]) { return false; }
    }
    
    if is_regional_indicator(left) && is_regional_indicator(right) {
        let mut count = 1;
        if pos >= 2 {
            let mut k = pos - 2;
            loop {
                if is_regional_indicator(scalars[k]) {
                    count += 1;
                    if k == 0 { break; }
                    k -= 1;
                } else {
                    break;
                }
            }
        }
        return count % 2 == 1;
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

fn longest_match(scalars: &[u32], grapheme_to_scalar: &[usize], i: usize, j: usize, num_graphemes: usize) -> usize {
    let mut l = 0;
    while i + l < num_graphemes && j + l < num_graphemes {
        let i_start = grapheme_to_scalar[i + l];
        let i_end = grapheme_to_scalar[i + l + 1];
        let j_start = grapheme_to_scalar[j + l];
        let j_end = grapheme_to_scalar[j + l + 1];
        
        if i_end - i_start != j_end - j_start { break; }
        
        let mut same = true;
        for m in 0..(i_end - i_start) {
            if scalars[i_start + m] != scalars[j_start + m] {
                same = false;
                break;
            }
        }
        if !same { break; }
        l += 1;
    }
    l
}