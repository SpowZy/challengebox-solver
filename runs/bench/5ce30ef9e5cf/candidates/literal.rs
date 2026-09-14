use std::collections::HashMap;
use std::io::{self, BufRead};

#[derive(Clone, Debug)]
enum Value {
    Integer(i64),
    ObjectRef(u32),
}

fn resolve_path(root: u32, attrs: &[u32], cells: &HashMap<(u32, u32), Value>) -> (u32, u32) {
    let mut current_obj = root;
    for i in 0..attrs.len() - 1 {
        let attr = attrs[i];
        if let Some(Value::ObjectRef(next_obj)) = cells.get(&(current_obj, attr)) {
            current_obj = *next_obj;
        }
    }
    let target_attr = attrs[attrs.len() - 1];
    (current_obj, target_attr)
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let _n = parts[0].parse::<u32>().unwrap();
    let _k = parts[1].parse::<usize>().unwrap();
    let _q = parts[2].parse::<usize>().unwrap();
    
    let mut cells: HashMap<(u32, u32), Value> = HashMap::new();
    
    for _ in 0.._k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let object = parts[0].parse::<u32>().unwrap();
        let attribute = parts[1].parse::<u32>().unwrap();
        let kind = parts[2];
        let value = parts[3];
        
        let cell_value = if kind == "I" {
            Value::Integer(value.parse::<i64>().unwrap())
        } else {
            Value::ObjectRef(value.parse::<u32>().unwrap())
        };
        
        cells.insert((object, attribute), cell_value);
    }
    
    let mut active_activations: Vec<(u32, Vec<((u32, u32), Value)>)> = Vec::new();
    
    for _ in 0.._q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        match parts[0] {
            "START" => {
                let id = parts[1].parse::<u32>().unwrap();
                let m = parts[2].parse::<usize>().unwrap();
                
                let mut activation_changes = Vec::new();
                let mut part_idx = 3;
                
                for _ in 0..m {
                    let root = parts[part_idx].parse::<u32>().unwrap();
                    let l = parts[part_idx + 1].parse::<usize>().unwrap();
                    part_idx += 2;
                    
                    let mut attrs = Vec::new();
                    for _ in 0..l {
                        attrs.push(parts[part_idx].parse::<u32>().unwrap());
                        part_idx += 1;
                    }
                    
                    let kind = parts[part_idx];
                    let value = parts[part_idx + 1];
                    part_idx += 2;
                    
                    let replacement_value = if kind == "I" {
                        Value::Integer(value.parse::<i64>().unwrap())
                    } else {
                        Value::ObjectRef(value.parse::<u32>().unwrap())
                    };
                    
                    let (obj, attr) = resolve_path(root, &attrs, &cells);
                    let target_cell = (obj, attr);
                    
                    let current_value = cells.get(&target_cell).cloned().unwrap();
                    activation_changes.push((target_cell, current_value));
                    
                    cells.insert(target_cell, replacement_value);
                }
                
                active_activations.push((id, activation_changes));
            }
            "STOP" => {
                let id = parts[1].parse::<u32>().unwrap();
                
                if let Some(pos) = active_activations.iter().position(|(aid, _)| *aid == id) {
                    let (_, changes) = active_activations.remove(pos);
                    
                    for (cell_key, original_value) in changes.iter().rev() {
                        cells.insert(*cell_key, original_value.clone());
                    }
                }
            }
            "STOPALL" => {
                while !active_activations.is_empty() {
                    let (_, changes) = active_activations.pop().unwrap();
                    
                    for (cell_key, original_value) in changes.iter().rev() {
                        cells.insert(*cell_key, original_value.clone());
                    }
                }
            }
            "GET" => {
                let root = parts[1].parse::<u32>().unwrap();
                let l = parts[2].parse::<usize>().unwrap();
                
                let mut attrs = Vec::new();
                for i in 0..l {
                    attrs.push(parts[3 + i].parse::<u32>().unwrap());
                }
                
                let (obj, attr) = resolve_path(root, &attrs, &cells);
                let target_cell = (obj, attr);
                
                if let Some(value) = cells.get(&target_cell) {
                    match value {
                        Value::Integer(i) => println!("I {}", i),
                        Value::ObjectRef(o) => println!("O {}", o),
                    }
                }
            }
            "STACK" => {
                print!("{}", active_activations.len());
                for (id, _) in &active_activations {
                    print!(" {}", id);
                }
                println!();
            }
            _ => {}
        }
    }
}