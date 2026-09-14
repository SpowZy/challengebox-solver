use std::collections::HashMap;
use std::io::{self, BufRead};

#[derive(Clone)]
struct Cell {
    kind: char,
    value: i64,
}

fn main() {
    let stdin = io::stdin();
    let mut reader = stdin.lock();
    let mut line = String::new();
    
    reader.read_line(&mut line).unwrap();
    let parts: Vec<&str> = line.trim().split_whitespace().collect();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    let mut cells: HashMap<(u32, u32), Cell> = HashMap::new();
    
    for _ in 0..k {
        line.clear();
        reader.read_line(&mut line).unwrap();
        let parts: Vec<&str> = line.trim().split_whitespace().collect();
        let object: u32 = parts[0].parse().unwrap();
        let attribute: u32 = parts[1].parse().unwrap();
        let kind: char = parts[2].chars().next().unwrap();
        let value: i64 = parts[3].parse().unwrap();
        cells.insert((object, attribute), Cell { kind, value });
    }
    
    let mut active_activations: Vec<u32> = Vec::new();
    let mut activation_writes: HashMap<u32, Vec<((u32, u32), Cell)>> = HashMap::new();
    
    for _ in 0..q {
        line.clear();
        reader.read_line(&mut line).unwrap();
        let parts: Vec<&str> = line.trim().split_whitespace().collect();
        
        match parts[0] {
            "START" => {
                let id: u32 = parts[1].parse().unwrap();
                let m: usize = parts[2].parse().unwrap();
                let mut writes = Vec::new();
                let mut idx = 3;
                
                for _ in 0..m {
                    let root: u32 = parts[idx].parse().unwrap();
                    idx += 1;
                    let l: usize = parts[idx].parse().unwrap();
                    idx += 1;
                    
                    let mut current_obj = root;
                    for _ in 0..l - 1 {
                        let attr: u32 = parts[idx].parse().unwrap();
                        idx += 1;
                        current_obj = cells.get(&(current_obj, attr)).unwrap().value as u32;
                    }
                    
                    let target_attr: u32 = parts[idx].parse().unwrap();
                    idx += 1;
                    let kind: char = parts[idx].chars().next().unwrap();
                    idx += 1;
                    let value: i64 = parts[idx].parse().unwrap();
                    idx += 1;
                    
                    let target_key = (current_obj, target_attr);
                    let old_value = cells.get(&target_key).unwrap().clone();
                    writes.push((target_key, old_value));
                    cells.insert(target_key, Cell { kind, value });
                }
                
                active_activations.push(id);
                activation_writes.insert(id, writes);
            }
            "STOP" => {
                let id: u32 = parts[1].parse().unwrap();
                if let Some(pos) = active_activations.iter().position(|&x| x == id) {
                    active_activations.remove(pos);
                    if let Some(writes) = activation_writes.remove(&id) {
                        for (key, value) in writes.iter().rev() {
                            cells.insert(*key, value.clone());
                        }
                    }
                }
            }
            "STOPALL" => {
                while !active_activations.is_empty() {
                    let id = active_activations.pop().unwrap();
                    if let Some(writes) = activation_writes.remove(&id) {
                        for (key, value) in writes.iter().rev() {
                            cells.insert(*key, value.clone());
                        }
                    }
                }
            }
            "GET" => {
                let root: u32 = parts[1].parse().unwrap();
                let l: usize = parts[2].parse().unwrap();
                let mut current_obj = root;
                for i in 0..l - 1 {
                    let attr: u32 = parts[3 + i].parse().unwrap();
                    current_obj = cells.get(&(current_obj, attr)).unwrap().value as u32;
                }
                let target_attr: u32 = parts[3 + l - 1].parse().unwrap();
                let cell = cells.get(&(current_obj, target_attr)).unwrap();
                println!("{} {}", cell.kind, cell.value);
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