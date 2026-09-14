use std::collections::BTreeMap;
use std::io::{self, BufRead};

#[derive(Clone, Debug)]
enum Cell {
    I(i64),
    O(u32),
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let _n: u32 = parts[0].parse().unwrap();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    let mut cells: BTreeMap<(u32, u32), Cell> = BTreeMap::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let obj: u32 = parts[0].parse().unwrap();
        let attr: u32 = parts[1].parse().unwrap();
        let kind = parts[2];
        let value_str = parts[3];
        
        let cell = if kind == "I" {
            Cell::I(value_str.parse().unwrap())
        } else {
            Cell::O(value_str.parse().unwrap())
        };
        
        cells.insert((obj, attr), cell);
    }
    
    let mut activations: BTreeMap<u32, Vec<((u32, u32), Option<Cell>)>> = BTreeMap::new();
    let mut activation_order: Vec<u32> = Vec::new();
    
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
                    idx += 1;
                    let l: usize = parts[idx].parse().unwrap();
                    idx += 1;
                    
                    let mut attrs: Vec<u32> = Vec::new();
                    for _ in 0..l {
                        attrs.push(parts[idx].parse().unwrap());
                        idx += 1;
                    }
                    
                    let kind = parts[idx];
                    idx += 1;
                    let value: i64 = parts[idx].parse().unwrap();
                    idx += 1;
                    
                    let new_cell = if kind == "I" {
                        Cell::I(value)
                    } else {
                        Cell::O(value as u32)
                    };
                    
                    replacements.push((root, attrs, new_cell));
                }
                
                let mut remembered = Vec::new();
                
                for (root, attrs, new_cell) in replacements {
                    let mut current_obj = root;
                    for i in 0..attrs.len() - 1 {
                        let attr = attrs[i];
                        match cells.get(&(current_obj, attr)) {
                            Some(Cell::O(next_obj)) => current_obj = *next_obj,
                            _ => {}
                        }
                    }
                    
                    let target_attr = attrs[attrs.len() - 1];
                    let target_key = (current_obj, target_attr);
                    
                    let current_value = cells.get(&target_key).cloned();
                    remembered.push((target_key.clone(), current_value));
                    
                    cells.insert(target_key, new_cell);
                }
                
                activations.insert(id, remembered);
                activation_order.push(id);
            }
            "STOP" => {
                let id: u32 = parts[1].parse().unwrap();
                
                if let Some(remembered) = activations.remove(&id) {
                    for (key, value) in remembered.iter().rev() {
                        match value {
                            Some(v) => cells.insert(key.clone(), v.clone()),
                            None => cells.remove(key),
                        };
                    }
                    
                    activation_order.retain(|&x| x != id);
                }
            }
            "STOPALL" => {
                let ids: Vec<u32> = activation_order.iter().rev().cloned().collect();
                for id in ids {
                    if let Some(remembered) = activations.remove(&id) {
                        for (key, value) in remembered.iter().rev() {
                            match value {
                                Some(v) => cells.insert(key.clone(), v.clone()),
                                None => cells.remove(key),
                            };
                        }
                        activation_order.retain(|&x| x != id);
                    }
                }
            }
            "GET" => {
                let root: u32 = parts[1].parse().unwrap();
                let l: usize = parts[2].parse().unwrap();
                
                let mut attrs: Vec<u32> = Vec::new();
                for i in 0..l {
                    attrs.push(parts[3 + i].parse().unwrap());
                }
                
                let mut current_obj = root;
                for i in 0..l - 1 {
                    let attr = attrs[i];
                    if let Some(Cell::O(next_obj)) = cells.get(&(current_obj, attr)) {
                        current_obj = *next_obj;
                    }
                }
                
                let cell = cells.get(&(current_obj, attrs[l - 1])).unwrap();
                
                match cell {
                    Cell::I(x) => println!("I {}", x),
                    Cell::O(x) => println!("O {}", x),
                }
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