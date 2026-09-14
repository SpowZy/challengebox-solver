use std::collections::HashMap;
use std::io::{self, BufRead};

#[derive(Clone, Debug)]
enum CellValue {
    Integer(i64),
    Object(u32),
}

fn resolve_path(
    cells: &HashMap<(u32, u32), CellValue>,
    root: u32,
    attrs: &[u32],
) -> (u32, u32) {
    let mut current_obj = root;
    for i in 0..attrs.len() - 1 {
        let attr = attrs[i];
        let cell_key = (current_obj, attr);
        match cells.get(&cell_key) {
            Some(CellValue::Object(next_obj)) => {
                current_obj = *next_obj;
            }
            _ => panic!("Invalid path"),
        }
    }
    (current_obj, attrs[attrs.len() - 1])
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
        let attribute: u32 = parts[1].parse().unwrap();
        let kind = parts[2];
        let value = parts[3];
        
        let cell_value = if kind == "I" {
            CellValue::Integer(value.parse().unwrap())
        } else {
            CellValue::Object(value.parse().unwrap())
        };
        
        cells.insert((object, attribute), cell_value);
    }
    
    let mut activations: HashMap<u32, Vec<((u32, u32), CellValue)>> = HashMap::new();
    let mut activation_order: Vec<u32> = Vec::new();
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let tokens: Vec<&str> = line.split_whitespace().collect();
        
        match tokens[0] {
            "START" => {
                let id: u32 = tokens[1].parse().unwrap();
                let m: usize = tokens[2].parse().unwrap();
                
                let mut idx = 3;
                let mut activation_record = Vec::new();
                
                for _ in 0..m {
                    let root: u32 = tokens[idx].parse().unwrap();
                    idx += 1;
                    let l: usize = tokens[idx].parse().unwrap();
                    idx += 1;
                    
                    let mut attrs = Vec::new();
                    for _ in 0..l {
                        attrs.push(tokens[idx].parse::<u32>().unwrap());
                        idx += 1;
                    }
                    
                    let kind = tokens[idx];
                    idx += 1;
                    let value = tokens[idx];
                    idx += 1;
                    
                    let cell_value = if kind == "I" {
                        CellValue::Integer(value.parse().unwrap())
                    } else {
                        CellValue::Object(value.parse().unwrap())
                    };
                    
                    let (target_obj, target_attr) = resolve_path(&cells, root, &attrs);
                    let cell_key = (target_obj, target_attr);
                    
                    let old_value = cells.get(&cell_key).cloned().unwrap();
                    activation_record.push((cell_key, old_value));
                    
                    cells.insert(cell_key, cell_value);
                }
                
                activations.insert(id, activation_record);
                activation_order.push(id);
            }
            "STOP" => {
                let id: u32 = tokens[1].parse().unwrap();
                
                if let Some(record) = activations.remove(&id) {
                    for (cell_key, old_value) in record.iter().rev() {
                        cells.insert(*cell_key, old_value.clone());
                    }
                    activation_order.retain(|&x| x != id);
                }
            }
            "STOPALL" => {
                while let Some(id) = activation_order.pop() {
                    if let Some(record) = activations.remove(&id) {
                        for (cell_key, old_value) in record.iter().rev() {
                            cells.insert(*cell_key, old_value.clone());
                        }
                    }
                }
            }
            "GET" => {
                let root: u32 = tokens[1].parse().unwrap();
                let l: usize = tokens[2].parse().unwrap();
                
                let mut attrs = Vec::new();
                for i in 0..l {
                    attrs.push(tokens[3 + i].parse::<u32>().unwrap());
                }
                
                let (target_obj, target_attr) = resolve_path(&cells, root, &attrs);
                let cell_key = (target_obj, target_attr);
                
                if let Some(value) = cells.get(&cell_key) {
                    match value {
                        CellValue::Integer(i) => println!("I {}", i),
                        CellValue::Object(o) => println!("O {}", o),
                    }
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