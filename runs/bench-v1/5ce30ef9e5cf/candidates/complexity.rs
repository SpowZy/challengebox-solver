use std::collections::HashMap;
use std::io::{self, BufRead};

#[derive(Clone)]
enum Value {
    I(i64),
    O(u32),
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let _n: usize = parts[0].parse().unwrap();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    let mut cells: HashMap<(u32, u32), Value> = HashMap::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let object: u32 = parts[0].parse().unwrap();
        let attribute: u32 = parts[1].parse().unwrap();
        let kind = parts[2];
        let value: i64 = parts[3].parse().unwrap();
        
        let val = if kind == "I" {
            Value::I(value)
        } else {
            Value::O(value as u32)
        };
        
        cells.insert((object, attribute), val);
    }
    
    let mut active_activations: Vec<u32> = Vec::new();
    let mut remembered: HashMap<u32, Vec<((u32, u32), Value)>> = HashMap::new();
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let tokens: Vec<&str> = line.split_whitespace().collect();
        
        match tokens[0] {
            "START" => {
                let id: u32 = tokens[1].parse().unwrap();
                let m: usize = tokens[2].parse().unwrap();
                
                let mut offset = 3;
                let mut remembered_writes = Vec::new();
                
                for _ in 0..m {
                    let root: u32 = tokens[offset].parse().unwrap();
                    let l: usize = tokens[offset + 1].parse().unwrap();
                    
                    let mut current = root;
                    for i in 0..l - 1 {
                        let attr: u32 = tokens[offset + 2 + i].parse().unwrap();
                        if let Value::O(next_obj) = cells.get(&(current, attr)).unwrap() {
                            current = *next_obj;
                        }
                    }
                    
                    let target_attr: u32 = tokens[offset + 2 + l - 1].parse().unwrap();
                    let cell_key = (current, target_attr);
                    
                    let current_val = cells.get(&cell_key).cloned().unwrap();
                    remembered_writes.push((cell_key, current_val));
                    
                    let kind = tokens[offset + 2 + l];
                    let value: i64 = tokens[offset + 3 + l].parse().unwrap();
                    
                    let new_val = if kind == "I" {
                        Value::I(value)
                    } else {
                        Value::O(value as u32)
                    };
                    cells.insert(cell_key, new_val);
                    
                    offset += 4 + l;
                }
                
                active_activations.push(id);
                remembered.insert(id, remembered_writes);
            }
            "STOP" => {
                let id: u32 = tokens[1].parse().unwrap();
                
                if let Some(pos) = active_activations.iter().position(|&x| x == id) {
                    active_activations.remove(pos);
                    
                    if let Some(writes) = remembered.remove(&id) {
                        for (cell_key, value) in writes.iter().rev() {
                            cells.insert(*cell_key, value.clone());
                        }
                    }
                }
            }
            "STOPALL" => {
                while !active_activations.is_empty() {
                    let id = active_activations.pop().unwrap();
                    
                    if let Some(writes) = remembered.remove(&id) {
                        for (cell_key, value) in writes.iter().rev() {
                            cells.insert(*cell_key, value.clone());
                        }
                    }
                }
            }
            "GET" => {
                let root: u32 = tokens[1].parse().unwrap();
                let l: usize = tokens[2].parse().unwrap();
                
                let mut current = root;
                for i in 0..l - 1 {
                    let attr: u32 = tokens[3 + i].parse().unwrap();
                    if let Value::O(next_obj) = cells.get(&(current, attr)).unwrap() {
                        current = *next_obj;
                    }
                }
                
                let target_attr: u32 = tokens[3 + l - 1].parse().unwrap();
                let cell_val = cells.get(&(current, target_attr)).unwrap();
                
                match cell_val {
                    Value::I(x) => println!("I {}", x),
                    Value::O(x) => println!("O {}", x),
                }
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