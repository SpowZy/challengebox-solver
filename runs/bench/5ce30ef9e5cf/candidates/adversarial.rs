use std::collections::HashMap;
use std::io::{self, BufRead};

#[derive(Clone, Debug)]
enum Value {
    Integer(i64),
    ObjectRef(i32),
}

fn main() {
    let stdin = io::stdin();
    let mut reader = stdin.lock().lines();
    
    let first_line = reader.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let _n: i32 = parts[0].parse().unwrap();
    let k: i32 = parts[1].parse().unwrap();
    let q: i32 = parts[2].parse().unwrap();
    
    let mut cells: HashMap<(i32, i32), Value> = HashMap::new();
    
    for _ in 0..k {
        let line = reader.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let object: i32 = parts[0].parse().unwrap();
        let attribute: i32 = parts[1].parse().unwrap();
        let kind = parts[2];
        let value = parts[3];
        
        let val = if kind == "I" {
            Value::Integer(value.parse().unwrap())
        } else {
            Value::ObjectRef(value.parse().unwrap())
        };
        
        cells.insert((object, attribute), val);
    }
    
    let mut activations: HashMap<i32, Vec<((i32, i32), Value)>> = HashMap::new();
    let mut activation_order: Vec<i32> = Vec::new();
    
    for _ in 0..q {
        let line = reader.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        match parts[0] {
            "START" => {
                let id: i32 = parts[1].parse().unwrap();
                let m: i32 = parts[2].parse().unwrap();
                
                let mut remembered: Vec<((i32, i32), Value)> = Vec::new();
                let mut idx = 3;
                
                for _ in 0..m {
                    let root: i32 = parts[idx].parse().unwrap();
                    let l: i32 = parts[idx + 1].parse().unwrap();
                    
                    let mut current_obj = root;
                    for i in 0..(l - 1) {
                        let attr: i32 = parts[idx + 2 + i as usize].parse().unwrap();
                        if let Some(Value::ObjectRef(next_obj)) = cells.get(&(current_obj, attr)) {
                            current_obj = *next_obj;
                        }
                    }
                    
                    let last_attr: i32 = parts[idx + 2 + (l - 1) as usize].parse().unwrap();
                    let cell_key = (current_obj, last_attr);
                    
                    let kind = parts[idx + 2 + l as usize];
                    let value_str = parts[idx + 2 + l as usize + 1];
                    
                    let new_val = if kind == "I" {
                        Value::Integer(value_str.parse().unwrap())
                    } else {
                        Value::ObjectRef(value_str.parse().unwrap())
                    };
                    
                    let current_val = cells.get(&cell_key).cloned().unwrap();
                    remembered.push((cell_key, current_val));
                    
                    cells.insert(cell_key, new_val);
                    
                    idx += 2 + l as usize + 2;
                }
                
                activations.insert(id, remembered);
                activation_order.push(id);
            }
            "STOP" => {
                let id: i32 = parts[1].parse().unwrap();
                
                if let Some(remembered) = activations.remove(&id) {
                    for (cell_key, val) in remembered.iter().rev() {
                        cells.insert(*cell_key, val.clone());
                    }
                    activation_order.retain(|&x| x != id);
                }
            }
            "STOPALL" => {
                let ids: Vec<i32> = activation_order.iter().rev().copied().collect();
                
                for id in ids {
                    if let Some(remembered) = activations.remove(&id) {
                        for (cell_key, val) in remembered.iter().rev() {
                            cells.insert(*cell_key, val.clone());
                        }
                    }
                }
                
                activation_order.clear();
            }
            "GET" => {
                let root: i32 = parts[1].parse().unwrap();
                let l: i32 = parts[2].parse().unwrap();
                
                let mut current_obj = root;
                for i in 0..(l - 1) {
                    let attr: i32 = parts[3 + i as usize].parse().unwrap();
                    if let Some(Value::ObjectRef(next_obj)) = cells.get(&(current_obj, attr)) {
                        current_obj = *next_obj;
                    }
                }
                
                let last_attr: i32 = parts[3 + (l - 1) as usize].parse().unwrap();
                let cell_val = cells.get(&(current_obj, last_attr)).unwrap();
                
                match cell_val {
                    Value::Integer(x) => println!("I {}", x),
                    Value::ObjectRef(x) => println!("O {}", x),
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