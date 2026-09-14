fn main() {
    use std::io::Read;
    
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).unwrap();
    let mut tokens = input.split_whitespace();
    
    let s = tokens.next().unwrap();
    let q: usize = tokens.next().unwrap().parse().unwrap();
    
    let scalars: Vec<u32> = s.chars().map(|c| c as u32).collect();
    let n = scalars.len();
    
    if n == 0 {
        return;
    }
    
    fn is_control(c: u32) -> bool {
        (c >= 0x0000 && c <= 0x001F) || (c >= 0x007F && c <= 0x009F)
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
    
    fn has_boundary(left: u32, right: u32, scalars: &[u32], pos: usize) -> bool {
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
            let mut idx = pos as i32 - 2;
            while idx >= 0 && is_attachment(scalars[idx as usize]) {
                idx -= 1;
            }
            if idx >= 0 && is_emoji(scalars[idx as usize]) {
                return false;
            }
        }
        
        if is_regional_indicator(left) && is_regional_indicator(right) {
            let mut count = 1;
            let mut idx = pos as i32 - 2;
            while idx >= 0 && is_regional_indicator(scalars[idx as usize]) {
                count += 1;
                idx -= 1;
            }
            return count % 2 == 0;
        }
        
        true
    }
    
    let mut grapheme_starts: Vec<usize> = vec![0];
    for i in 1..n {
        if has_boundary(scalars[i-1], scalars[i], &scalars, i) {
            grapheme_starts.push(i);
        }
    }
    let num_graphemes = grapheme_starts.len();
    
    let mut utf16_offsets: Vec<usize> = Vec::with_capacity(n + 1);
    utf16_offsets.push(0);
    for i in 0..n {
        let count = if scalars[i] <= 0xFFFF { 1 } else { 2 };
        utf16_offsets.push(utf16_offsets[i] + count);
    }
    
    let mut boundary_offsets: Vec<usize> = Vec::with_capacity(num_graphemes + 1);
    for &start in &grapheme_starts {
        boundary_offsets.push(utf16_offsets[start]);
    }
    boundary_offsets.push(utf16_offsets[n]);
    
    for _ in 0..q {
        let query_type: u32 = tokens.next().unwrap().parse().unwrap();
        let a: i64 = tokens.next().unwrap().parse().unwrap();
        let b: i64 = tokens.next().unwrap().parse().unwrap();
        
        let mut i = a;
        if i < 0 {
            i += num_graphemes as i64;
        }
        i = i.max(0).min(num_graphemes as i64);
        
        let mut j = b;
        if j < 0 {
            j += num_graphemes as i64;
        }
        j = j.max(0).min(num_graphemes as i64);
        
        if query_type == 1 {
            if j < i {
                let offset = boundary_offsets[i as usize];
                println!("{} {}", offset, offset);
            } else {
                println!("{} {}", boundary_offsets[i as usize], boundary_offsets[j as usize]);
            }
        } else {
            let max_k = (num_graphemes as i64 - i.max(j)) as usize;
            let mut l = 0;
            
            for k in 0..=max_k {
                let gi = (i + k as i64) as usize;
                let gj = (j + k as i64) as usize;
                
                if gi >= num_graphemes || gj >= num_graphemes {
                    break;
                }
                
                let start_i = grapheme_starts[gi];
                let end_i = if gi + 1 < grapheme_starts.len() { grapheme_starts[gi + 1] } else { n };
                let start_j = grapheme_starts[gj];
                let end_j = if gj + 1 < grapheme_starts.len() { grapheme_starts[gj + 1] } else { n };
                
                if scalars[start_i..end_i] == scalars[start_j..end_j] {
                    l = k + 1;
                } else {
                    break;
                }
            }
            
            let start_scalar = grapheme_starts[i as usize];
            let end_scalar = if (i as usize) + l < num_graphemes { 
                grapheme_starts[(i as usize) + l]
            } else {
                n
            };
            let utf16_units = utf16_offsets[end_scalar] - utf16_offsets[start_scalar];
            
            println!("{} {}", l, utf16_units);
        }
    }
}