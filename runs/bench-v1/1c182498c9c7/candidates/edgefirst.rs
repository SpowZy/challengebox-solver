use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut tokens = input.split_whitespace();

    let n: usize = tokens.next().unwrap().parse().unwrap();
    let s: usize = tokens.next().unwrap().parse().unwrap();
    let q: usize = tokens.next().unwrap().parse().unwrap();
    let c: u64 = tokens.next().unwrap().parse().unwrap();
    let h: u64 = tokens.next().unwrap().parse().unwrap();

    let mut byte_widths = Vec::new();
    for _ in 0..n {
        let hex = tokens.next().unwrap();
        let code_point = u32::from_str_radix(hex, 16).unwrap();
        let width: u64 = if code_point <= 0x7F {
            1
        } else if code_point <= 0x7FF {
            2
        } else if code_point <= 0xFFFF {
            3
        } else {
            4
        };
        byte_widths.push(width);
    }

    let mut segment_ends = Vec::new();
    let mut pos = 0;
    for _ in 0..s {
        let len: usize = tokens.next().unwrap().parse().unwrap();
        pos += len;
        segment_ends.push(pos - 1);
    }

    for _ in 0..q {
        let l: usize = tokens.next().unwrap().parse().unwrap();
        let r: usize = tokens.next().unwrap().parse().unwrap();
        let b: u64 = tokens.next().unwrap().parse().unwrap();

        let l_idx = l - 1;
        let r_idx = r - 1;

        let mut payload_bytes = 0u64;
        let mut wire_bytes = 0u64;
        let mut sent_count = 0usize;
        let mut chunks = 0u64;
        let mut last_chunk_payload = 0u64;

        let mut chunk_start_idx = l_idx;
        let mut chunk_payload = 0u64;

        for pos in l_idx..=r_idx {
            let need_new_chunk = if pos == l_idx {
                true
            } else {
                let chunk_exceeds_capacity = chunk_payload.saturating_add(byte_widths[pos]) > c;
                let crosses_boundary = {
                    let chunk_seg = segment_ends.iter().position(|&end| chunk_start_idx <= end).unwrap_or(segment_ends.len());
                    let pos_seg = segment_ends.iter().position(|&end| pos <= end).unwrap_or(segment_ends.len());
                    chunk_seg != pos_seg
                };
                chunk_exceeds_capacity || crosses_boundary
            };

            let wire_needed = byte_widths[pos] + if need_new_chunk { h } else { 0 };

            if wire_bytes.saturating_add(wire_needed) > b {
                break;
            }

            wire_bytes = wire_bytes.saturating_add(wire_needed);
            payload_bytes = payload_bytes.saturating_add(byte_widths[pos]);
            sent_count += 1;

            if need_new_chunk {
                chunks += 1;
                chunk_start_idx = pos;
                chunk_payload = byte_widths[pos];
                last_chunk_payload = byte_widths[pos];
            } else {
                chunk_payload = chunk_payload.saturating_add(byte_widths[pos]);
                last_chunk_payload = last_chunk_payload.saturating_add(byte_widths[pos]);
            }
        }

        let cause = if sent_count == r_idx - l_idx + 1 { "END" } else { "LIMIT" };
        let last_pos = if sent_count > 0 { l_idx + sent_count } else { 0 };

        println!(
            "{} {} {} {} {} {} {}",
            payload_bytes, wire_bytes, sent_count, last_pos, chunks, last_chunk_payload, cause
        );
    }
}