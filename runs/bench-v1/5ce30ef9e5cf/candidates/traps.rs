use std::collections::HashMap;
use std::io::{self, BufRead};

#[derive(Clone)]
enum Cell {
    I(i64),
    O(u32),
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    let mut cells: HashMap<(u32, u32), Cell> = HashMap::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let obj: u32 = parts[0].parse().unwrap();
        let attr: u32 = parts[1].parse().unwrap();
        let kind = parts[2];
        let value: String = parts[3].parse().unwrap();
        
        let cell = if kind == "I" {
            Cell::I(value.parse().unwrap())
        } else {
            Cell::O(value.parse().unwrap())
        };
        
        cells.insert((obj, attr), cell);
    }
    
    let mut activations: HashMap<u32, Vec<((u32, u32), Option<Cell>)>> = HashMap::new();
    let mut active_stack: Vec<u32> = Vec::new();
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        match parts[0] {
            "START" => {
                let id: u32 = parts[1].parse().unwrap();
                let m: usize = parts[2].parse().unwrap();
                
                let mut replacements = Vec::new();
                let mut idx = 3;
                
                for _ in 0..m {
                    let root: u32 = parts[idx].parse().unwrap();
                    let l: usize = parts[idx + 1].parse().unwrap();
                    idx += 2;
                    
                    let mut attributes = Vec::new();
                    for _ in 0..l {
                        attributes.push(parts[idx].parse::<u32>().unwrap());
                        idx += 1;
                    }
                    
                    let kind = parts[idx];
                    let value: String = parts[idx + 1].parse().unwrap();
                    idx += 2;
                    
                    let new_cell = if kind == "I" {
                        Cell::I(value.parse().unwrap())
                    } else {
                        Cell::O(value.parse().unwrap())
                    };
                    
                    let mut current_obj = root;
                    for i in 0..l - 1 {
                        let attr = attributes[i];
                        if let Some(Cell::O(next_obj)) = cells.get(&(current_obj, attr)) {
                            current_obj = *next_obj;
                        }
                    }
                    
                    let final_key = (current_obj, attributes[l - 1]);
                    let old_value = cells.get(&final_key).cloned();
                    cells.insert(final_key, new_cell);
                    
                    replacements.push((final_key, old_value));
                }
                
                activations.insert(id, replacements);
                active_stack.push(id);
            }
            "STOP" => {
                let id: u32 = parts[1].parse().unwrap();
                
                if let Some(pos) = active_stack.iter().position(|&x| x == id) {
                    active_stack.remove(pos);
                    if let Some(replacements) = activations.remove(&id) {
                        for (key, old_value) in replacements.iter().rev() {
                            match old_value {
                                Some(v) => cells.insert(*key, v.clone()),
                                None => cells.remove(key),
                            };
                        }
                    }
                }
            }
            "STOPALL" => {
                while let Some(id) = active_stack.pop() {
                    if let Some(replacements) = activations.remove(&id) {
                        for (key, old_value) in replacements.iter().rev() {
                            match old_value {
                                Some(v) => cells.insert(*key, v.clone()),
                                None => cells.remove(key),
                            };
                        }
                    }
                }
            }
            "GET" => {
                let root: u32 = parts[1].parse().unwrap();
                let l: usize = parts[2].parse().unwrap();
                
                let mut attributes = Vec::new();
                for i in 0..l {
                    attributes.push(parts[3 + i].parse::<u32>().unwrap());
                }
                
                let mut current_obj = root;
                for i in 0..l - 1 {
                    let attr = attributes[i];
                    if let Some(Cell::O(next_obj)) = cells.get(&(current_obj, attr)) {
                        current_obj = *next_obj;
                    }
                }
                
                let final_key = (current_obj, attributes[l - 1]);
                if let Some(cell) = cells.get(&final_key) {
                    match cell {
                        Cell::I(x) => println!("I {}", x),
                        Cell::O(x) => println!("O {}", x),
                    }
                }
            }
            "STACK" => {
                print!("{}", active_stack.len());
                for id in &active_stack {
                    print!(" {}", id);
                }
                println!();
            }
            _ => {}
        }
    }
}