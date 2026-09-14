use std::collections::HashMap;
use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let _n: usize = parts[0].parse().unwrap();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    let mut cells: HashMap<(i64, i64), (u8, i64)> = HashMap::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let obj: i64 = parts[0].parse().unwrap();
        let attr: i64 = parts[1].parse().unwrap();
        let kind: u8 = if parts[2] == "I" { 0 } else { 1 };
        let value: i64 = parts[3].parse().unwrap();
        cells.insert((obj, attr), (kind, value));
    }
    
    let mut activations: HashMap<i64, Vec<((i64, i64), (u8, i64))>> = HashMap::new();
    let mut activation_order: Vec<i64> = Vec::new();
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        match parts[0] {
            "START" => {
                let id: i64 = parts[1].parse().unwrap();
                let m: usize = parts[2].parse().unwrap();
                
                let mut idx = 3;
                let mut recorded = Vec::new();
                
                for _ in 0..m {
                    let root: i64 = parts[idx].parse().unwrap();
                    let l: usize = parts[idx + 1].parse().unwrap();
                    idx += 2;
                    
                    let mut path_attrs = Vec::new();
                    for _ in 0..l {
                        path_attrs.push(parts[idx].parse::<i64>().unwrap());
                        idx += 1;
                    }
                    
                    let kind: u8 = if parts[idx] == "I" { 0 } else { 1 };
                    let value: i64 = parts[idx + 1].parse().unwrap();
                    idx += 2;
                    
                    let mut current_obj = root;
                    for i in 0..path_attrs.len() - 1 {
                        let (_, next_obj) = cells.get(&(current_obj, path_attrs[i])).unwrap();
                        current_obj = *next_obj;
                    }
                    
                    let cell_loc = (current_obj, path_attrs[path_attrs.len() - 1]);
                    let current_val = cells.get(&cell_loc).copied().unwrap();
                    recorded.push((cell_loc, current_val));
                    cells.insert(cell_loc, (kind, value));
                }
                
                activations.insert(id, recorded);
                activation_order.push(id);
            }
            "STOP" => {
                let id: i64 = parts[1].parse().unwrap();
                if let Some(recorded) = activations.remove(&id) {
                    for (cell_loc, val) in recorded.iter().rev() {
                        cells.insert(*cell_loc, *val);
                    }
                    activation_order.retain(|&x| x != id);
                }
            }
            "STOPALL" => {
                let ids: Vec<i64> = activation_order.iter().rev().copied().collect();
                for id in ids {
                    if let Some(recorded) = activations.remove(&id) {
                        for (cell_loc, val) in recorded.iter().rev() {
                            cells.insert(*cell_loc, *val);
                        }
                    }
                }
                activation_order.clear();
            }
            "GET" => {
                let root: i64 = parts[1].parse().unwrap();
                let l: usize = parts[2].parse().unwrap();
                let mut current_obj = root;
                for i in 0..l - 1 {
                    let (_, next_obj) = cells.get(&(current_obj, parts[3 + i].parse::<i64>().unwrap())).unwrap();
                    current_obj = *next_obj;
                }
                let (kind, value) = cells.get(&(current_obj, parts[3 + l - 1].parse::<i64>().unwrap())).unwrap();
                println!("{} {}", if *kind == 0 { "I" } else { "O" }, value);
            }
            "STACK" => {
                print!("{}", activation_order.len());
                for id in &activation_order {
                    print!(" {}", id);
                }
                println!();
            }
            _ => {}
        }
    }
}