use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();

    let first = lines.next().unwrap().unwrap();
    let p: Vec<&str> = first.split_whitespace().collect();
    let n: usize = p[0].parse().unwrap();
    let s: usize = p[1].parse().unwrap();
    let q: usize = p[2].parse().unwrap();
    let c: u64 = p[3].parse().unwrap();
    let h: u64 = p[4].parse().unwrap();

    let mut cp: Vec<u32> = Vec::new();
    while cp.len() < n {
        let mut line = String::new();
        lines.next().unwrap().read_line(&mut line).unwrap();
        for t in line.split_whitespace() {
            if cp.len() < n {
                cp.push(u32::from_str_radix(t, 16).unwrap());
            }
        }
    }

    let sz: Vec<u64> = cp.iter().map(|&x| {
        if x <= 0x7F { 1 } else if x <= 0x7FF { 2 } else if x <= 0xFFFF { 3 } else { 4 }
    }).collect();

    let mut seg: Vec<usize> = Vec::new();
    while seg.len() < s {
        let mut line = String::new();
        lines.next().unwrap().read_line(&mut line).unwrap();
        for t in line.split_whitespace() {
            if seg.len() < s {
                seg.push(t.parse().unwrap());
            }
        }
    }

    let mut seg_end: Vec<usize> = Vec::new();
    let mut pos = 0;
    for &l in &seg {
        pos += l;
        seg_end.push(pos);
    }

    for _ in 0..q {
        let mut line = String::new();
        lines.next().unwrap().read_line(&mut line).unwrap();
        let p: Vec<&str> = line.split_whitespace().collect();
        let l: usize = p[0].parse().unwrap();
        let r: usize = p[1].parse().unwrap();
        let b: u64 = p[2].parse().unwrap();

        let start = l - 1;
        let end = r;

        let mut payload = 0u64;
        let mut headers = 0u64;
        let mut chars = 0u64;
        let mut last = 0u32;
        let mut chunks = 0u32;
        let mut last_cp = 0u64;
        let mut cur_cp = 0u64;
        let mut reason = "END";

        let mut si = 0;
        for (j, &e) in seg_end.iter().enumerate() {
            if start < e {
                si = j;
                break;
            }
        }

        for i in start..end {
            let s = sz[i];

            if i > start && i >= seg_end[si] {
                if cur_cp > 0 {
                    chunks += 1;
                    last_cp = cur_cp;
                    cur_cp = 0;
                }
                si += 1;
            }

            if cur_cp > 0 && cur_cp + s > c {
                chunks += 1;
                last_cp = cur_cp;
                cur_cp = 0;
            }

            let new_chunk = cur_cp == 0;
            let cost = (if new_chunk { h } else { 0 }) + s;
            if payload + headers + cur_cp + cost > b {
                reason = "LIMIT";
                break;
            }

            if new_chunk {
                headers += h;
            }
            payload += s;
            cur_cp += s;
            chars += 1;
            last = (i + 1) as u32;
        }

        if cur_cp > 0 {
            chunks += 1;
            last_cp = cur_cp;
        }

        let wire = payload + headers;
        println!("{} {} {} {} {} {} {}", payload, wire, chars, last, chunks, last_cp, reason);
    }
}