use std::collections::HashMap;
use std::io::{self, BufRead};

fn resolve_path(root: usize, attrs: &[u64], cells: &HashMap<(usize, u64), (char, i64)>) -> (usize, u64) {
    let mut current_obj = root;
    for (i, &attr) in attrs.iter().enumerate() {
        if i == attrs.len() - 1 {
            return (current_obj, attr);
        }
        let (kind, value) = cells.get(&(current_obj, attr)).expect("Invalid path");
        if kind != &'O' {
            panic!("Expected object reference");
        }
        current_obj = *value as usize;
    }
    unreachable!()
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let _n: usize = parts[0].parse().unwrap();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    let mut cells: HashMap<(usize, u64), (char, i64)> = HashMap::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let obj: usize = parts[0].parse().unwrap();
        let attr: u64 = parts[1].parse().unwrap();
        let kind = parts[2].chars().next().unwrap();
        let value: i64 = parts[3].parse().unwrap();
        cells.insert((obj, attr), (kind, value));
    }
    
    let mut active_activations: Vec<usize> = Vec::new();
    let mut activation_history: HashMap<usize, Vec<((usize, u64), (char, i64))>> = HashMap::new();
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let tokens: Vec<&str> = line.split_whitespace().collect();
        
        match tokens[0] {
            "START" => {
                let id: usize = tokens[1].parse().unwrap();
                let m: usize = tokens[2].parse().unwrap();
                
                let mut history = Vec::new();
                let mut token_idx = 3;
                
                for _ in 0..m {
                    let root: usize = tokens[token_idx].parse().unwrap();
                    let l: usize = tokens[token_idx + 1].parse().unwrap();
                    
                    let mut attrs = Vec::new();
                    for i in 0..l {
                        attrs.push(tokens[token_idx + 2 + i].parse::<u64>().unwrap());
                    }
                    
                    let kind = tokens[token_idx + 2 + l].chars().next().unwrap();
                    let value: i64 = tokens[token_idx + 2 + l + 1].parse().unwrap();
                    
                    let (obj, attr) = resolve_path(root, &attrs, &cells);
                    
                    if let Some(cv) = cells.get(&(obj, attr)) {
                        history.push(((obj, attr), *cv));
                    }
                    
                    cells.insert((obj, attr), (kind, value));
                    
                    token_idx += 2 + l + 2;
                }
                
                active_activations.push(id);
                activation_history.insert(id, history);
            }
            "STOP" => {
                let id: usize = tokens[1].parse().unwrap();
                
                if let Some(idx) = active_activations.iter().position(|&x| x == id) {
                    active_activations.remove(idx);
                    
                    if let Some(history) = activation_history.remove(&id) {
                        for (cell, value) in history.iter().rev() {
                            cells.insert(*cell, *value);
                        }
                    }
                }
            }
            "STOPALL" => {
                while !active_activations.is_empty() {
                    let id = active_activations.pop().unwrap();
                    if let Some(history) = activation_history.remove(&id) {
                        for (cell, value) in history.iter().rev() {
                            cells.insert(*cell, *value);
                        }
                    }
                }
            }
            "GET" => {
                let root: usize = tokens[1].parse().unwrap();
                let l: usize = tokens[2].parse().unwrap();
                
                let mut attrs = Vec::new();
                for i in 0..l {
                    attrs.push(tokens[3 + i].parse::<u64>().unwrap());
                }
                
                let (obj, attr) = resolve_path(root, &attrs, &cells);
                
                let (kind, value) = cells.get(&(obj, attr)).unwrap();
                println!("{} {}", kind, value);
            }
            "STACK" => {
                print!("{}", active_activations.len());
                for id in &active_activations {
                    print!(" {}", id);
                }
                println!();
            }
            _ => {}
        }
    }
}