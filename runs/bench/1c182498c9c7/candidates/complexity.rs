use std::io::{self, BufRead};

fn utf8_width(ch: u32) -> u8 {
    if ch <= 0x7F {
        1
    } else if ch <= 0x7FF {
        2
    } else if ch <= 0xFFFF {
        3
    } else {
        4
    }
}

fn find_segment(pos: usize, segment_ends: &[usize]) -> usize {
    for (i, &end) in segment_ends.iter().enumerate() {
        if pos <= end {
            return i;
        }
    }
    segment_ends.len() - 1
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();

    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let N: usize = parts[0].parse().unwrap();
    let S: usize = parts[1].parse().unwrap();
    let Q: usize = parts[2].parse().unwrap();
    let C: u64 = parts[3].parse().unwrap();
    let H: u64 = parts[4].parse().unwrap();

    let mut tokens = Vec::new();
    for line_result in lines {
        if let Ok(line) = line_result {
            for token in line.split_whitespace() {
                tokens.push(token.to_string());
            }
        }
    }

    let mut idx = 0;

    let mut chars = Vec::new();
    for _ in 0..N {
        let ch: u32 = u32::from_str_radix(&tokens[idx], 16).unwrap();
        chars.push(ch);
        idx += 1;
    }

    let mut segment_lengths = Vec::new();
    for _ in 0..S {
        let len: usize = tokens[idx].parse().unwrap();
        segment_lengths.push(len);
        idx += 1;
    }

    let mut segment_ends = Vec::new();
    let mut cumsum = 0;
    for &len in &segment_lengths {
        cumsum += len;
        segment_ends.push(cumsum);
    }

    for _ in 0..Q {
        let L: usize = tokens[idx].parse().unwrap();
        idx += 1;
        let R: usize = tokens[idx].parse().unwrap();
        idx += 1;
        let B: u64 = tokens[idx].parse().unwrap();
        idx += 1;

        let mut payload_bytes: u64 = 0;
        let mut wire_bytes: u64 = 0;
        let mut chunks: u64 = 0;
        let mut last_pos: usize = 0;
        let mut current_chunk_payload: u64 = 0;
        let mut last_chunk_payload: u64 = 0;
        let mut cause = "LIMIT";

        for pos in L..=R {
            let char_idx = pos - 1;
            let char_bytes = utf8_width(chars[char_idx]) as u64;

            let prev_segment = if pos > L {
                find_segment(pos - 1, &segment_ends)
            } else {
                find_segment(L, &segment_ends)
            };
            let curr_segment = find_segment(pos, &segment_ends);
            let segment_boundary = curr_segment != prev_segment;

            let would_exceed_chunk =
                current_chunk_payload.saturating_add(char_bytes) > C;

            if (would_exceed_chunk || segment_boundary) && current_chunk_payload > 0 {
                wire_bytes = wire_bytes
                    .saturating_add(current_chunk_payload)
                    .saturating_add(H);
                chunks += 1;
                last_chunk_payload = current_chunk_payload;
                current_chunk_payload = 0;
            }

            let new_chunk_header = if current_chunk_payload == 0 { H } else { 0 };
            let potential_wire = wire_bytes
                .saturating_add(new_chunk_header)
                .saturating_add(char_bytes);

            if potential_wire > B {
                cause = "LIMIT";
                break;
            }

            payload_bytes = payload_bytes.saturating_add(char_bytes);
            current_chunk_payload = current_chunk_payload.saturating_add(char_bytes);
            last_pos = pos;

            if pos == R {
                cause = "END";
            }
        }

        if current_chunk_payload > 0 {
            wire_bytes = wire_bytes
                .saturating_add(current_chunk_payload)
                .saturating_add(H);
            chunks += 1;
            last_chunk_payload = current_chunk_payload;
        }

        let num_chars = if last_pos >= L {
            last_pos - L + 1
        } else {
            0
        };

        println!(
            "{} {} {} {} {} {} {}",
            payload_bytes, wire_bytes, num_chars, last_pos, chunks, last_chunk_payload, cause
        );
    }
}