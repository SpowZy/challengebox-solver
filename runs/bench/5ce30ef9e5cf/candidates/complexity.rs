use std::collections::HashMap;
use std::io::{self, BufRead};

#[derive(Clone)]
enum CellValue {
    Integer(i64),
    ObjectRef(u32),
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let _n: u32 = parts[0].parse().unwrap();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    let mut cells: HashMap<(u32, u32), CellValue> = HashMap::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let object: u32 = parts[0].parse().unwrap();
        let attr: u32 = parts[1].parse().unwrap();
        let kind = parts[2];
        let value = parts[3];
        
        let cell_value = if kind == "I" {
            CellValue::Integer(value.parse().unwrap())
        } else {
            CellValue::ObjectRef(value.parse().unwrap())
        };
        
        cells.insert((object, attr), cell_value);
    }
    
    let mut activations: HashMap<u32, Vec<((u32, u32), CellValue)>> = HashMap::new();
    let mut activation_order: Vec<u32> = Vec::new();
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let cmd = parts[0];
        
        if cmd == "START" {
            let id: u32 = parts[1].parse().unwrap();
            let m: usize = parts[2].parse().unwrap();
            
            let mut changes = Vec::new();
            let mut idx = 3;
            
            for _ in 0..m {
                let root: u32 = parts[idx].parse().unwrap();
                let l: usize = parts[idx + 1].parse().unwrap();
                idx += 2;
                
                let mut path = Vec::new();
                for _ in 0..l {
                    path.push(parts[idx].parse::<u32>().unwrap());
                    idx += 1;
                }
                
                let kind = parts[idx];
                let value = parts[idx + 1];
                idx += 2;
                
                let new_value = if kind == "I" {
                    CellValue::Integer(value.parse().unwrap())
                } else {
                    CellValue::ObjectRef(value.parse().unwrap())
                };
                
                let mut current = root;
                for i in 0..l - 1 {
                    let attr = path[i];
                    if let CellValue::ObjectRef(next) = cells.get(&(current, attr))
                        .expect("Object reference expected").clone() {
                        current = next;
                    } else {
                        panic!("Expected object reference");
                    }
                }
                
                let target_attr = path[l - 1];
                let cell_key = (current, target_attr);
                let old_value = cells.get(&cell_key).cloned().expect("Cell should exist");
                
                cells.insert(cell_key, new_value);
                changes.push((cell_key, old_value));
            }
            
            activations.insert(id, changes);
            activation_order.push(id);
            
        } else if cmd == "STOP" {
            let id: u32 = parts[1].parse().unwrap();
            
            if let Some(changes) = activations.remove(&id) {
                for (cell_key, old_value) in changes.iter().rev() {
                    cells.insert(*cell_key, old_value.clone());
                }
                activation_order.retain(|&x| x != id);
            }
            
        } else if cmd == "STOPALL" {
            while let Some(id) = activation_order.pop() {
                if let Some(changes) = activations.remove(&id) {
                    for (cell_key, old_value) in changes.iter().rev() {
                        cells.insert(*cell_key, old_value.clone());
                    }
                }
            }
            
        } else if cmd == "GET" {
            let root: u32 = parts[1].parse().unwrap();
            let l: usize = parts[2].parse().unwrap();
            
            let mut path = Vec::new();
            for i in 0..l {
                path.push(parts[3 + i].parse::<u32>().unwrap());
            }
            
            let mut current = root;
            for i in 0..l - 1 {
                let attr = path[i];
                if let CellValue::ObjectRef(next) = cells.get(&(current, attr))
                    .expect("Object reference expected").clone() {
                    current = next;
                } else {
                    panic!("Expected object reference");
                }
            }
            
            let target_attr = path[l - 1];
            let cell_val = cells.get(&(current, target_attr))
                .expect("Cell should exist").clone();
            
            match cell_val {
                CellValue::Integer(x) => println!("I {}", x),
                CellValue::ObjectRef(x) => println!("O {}", x),
            }
            
        } else if cmd == "STACK" {
            print!("{}", activation_order.len());
            for id in &activation_order {
                print!(" {}", id);
            }
            println!();
        }
    }
}