use std::collections::{HashMap, VecDeque};
use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let n: usize = parts[0].parse().unwrap();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    let mut cells: HashMap<(u32, u32), (char, i64)> = HashMap::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let obj: u32 = parts[0].parse().unwrap();
        let attr: u32 = parts[1].parse().unwrap();
        let kind: char = parts[2].chars().next().unwrap();
        let value: i64 = parts[3].parse().unwrap();
        
        cells.insert((obj, attr), (kind, value));
    }
    
    let mut activations: HashMap<u32, Vec<((u32, u32), (char, i64))>> = HashMap::new();
    let mut activation_order: VecDeque<u32> = VecDeque::new();
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let tokens: Vec<&str> = line.split_whitespace().collect();
        
        let command = tokens[0];
        
        if command == "START" {
            let id: u32 = tokens[1].parse().unwrap();
            let m: usize = tokens[2].parse().unwrap();
            
            let mut activation_writes = Vec::new();
            let mut token_idx = 3;
            
            for _ in 0..m {
                let root: u32 = tokens[token_idx].parse().unwrap();
                let l: usize = tokens[token_idx + 1].parse().unwrap();
                token_idx += 2;
                
                let mut attrs = Vec::new();
                for _ in 0..l {
                    attrs.push(tokens[token_idx].parse::<u32>().unwrap());
                    token_idx += 1;
                }
                
                let kind: char = tokens[token_idx].chars().next().unwrap();
                let value: i64 = tokens[token_idx + 1].parse().unwrap();
                token_idx += 2;
                
                let mut current_obj = root;
                for i in 0..l-1 {
                    let attr = attrs[i];
                    let (_, obj_ref) = cells.get(&(current_obj, attr)).unwrap();
                    current_obj = *obj_ref as u32;
                }
                
                let target_attr = attrs[l-1];
                let target_cell = (current_obj, target_attr);
                
                let current_value = *cells.get(&target_cell).unwrap();
                cells.insert(target_cell, (kind, value));
                activation_writes.push((target_cell, current_value));
            }
            
            activations.insert(id, activation_writes);
            activation_order.push_back(id);
        } else if command == "STOP" {
            let id: u32 = tokens[1].parse().unwrap();
            
            if let Some(writes) = activations.remove(&id) {
                activation_order.retain(|&x| x != id);
                
                for (cell, value) in writes.into_iter().rev() {
                    cells.insert(cell, value);
                }
            }
        } else if command == "STOPALL" {
            let ids: Vec<u32> = activation_order.iter().copied().rev().collect();
            activation_order.clear();
            
            for id in ids {
                if let Some(writes) = activations.remove(&id) {
                    for (cell, value) in writes.into_iter().rev() {
                        cells.insert(cell, value);
                    }
                }
            }
        } else if command == "GET" {
            let root: u32 = tokens[1].parse().unwrap();
            let l: usize = tokens[2].parse().unwrap();
            
            let mut current_obj = root;
            for i in 0..l-1 {
                let attr: u32 = tokens[3 + i].parse().unwrap();
                let (_, obj_ref) = cells.get(&(current_obj, attr)).unwrap();
                current_obj = *obj_ref as u32;
            }
            
            let target_attr: u32 = tokens[3 + l - 1].parse().unwrap();
            let (kind, value) = cells.get(&(current_obj, target_attr)).unwrap();
            println!("{} {}", kind, value);
        } else if command == "STACK" {
            print!("{}", activation_order.len());
            for id in &activation_order {
                print!(" {}", id);
            }
            println!();
        }
    }
}