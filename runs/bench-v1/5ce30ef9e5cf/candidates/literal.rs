use std::collections::{HashMap, BTreeMap};
use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let _n: usize = parts[0].parse().unwrap();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    let mut cells: BTreeMap<(i64, i64), (bool, i64)> = BTreeMap::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let object: i64 = parts[0].parse().unwrap();
        let attribute: i64 = parts[1].parse().unwrap();
        let kind: char = parts[2].chars().next().unwrap();
        let value: i64 = parts[3].parse().unwrap();
        
        cells.insert((object, attribute), (kind == 'I', value));
    }
    
    type Change = ((i64, i64), Option<(bool, i64)>);
    let mut activations: Vec<(u32, Vec<Change>)> = Vec::new();
    let mut activation_map: HashMap<u32, usize> = HashMap::new();
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        match parts[0] {
            "START" => {
                let id: u32 = parts[1].parse().unwrap();
                let m: usize = parts[2].parse().unwrap();
                
                let mut idx = 3;
                let mut changes: Vec<Change> = Vec::new();
                
                for _ in 0..m {
                    let root: i64 = parts[idx].parse().unwrap();
                    let l: usize = parts[idx + 1].parse().unwrap();
                    
                    let mut current_obj = root;
                    let attributes: Vec<i64> = (0..l)
                        .map(|i| parts[idx + 2 + i].parse().unwrap())
                        .collect();
                    
                    for i in 0..(l - 1) {
                        let attr = attributes[i];
                        let (_, val) = cells.get(&(current_obj, attr)).unwrap();
                        current_obj = *val;
                    }
                    
                    let target_attr = attributes[l - 1];
                    let kind: char = parts[idx + 2 + l].chars().next().unwrap();
                    let value: i64 = parts[idx + 3 + l].parse().unwrap();
                    
                    let new_val = (kind == 'I', value);
                    let cell_addr = (current_obj, target_attr);
                    let old_val = cells.get(&cell_addr).cloned();
                    changes.push((cell_addr, old_val));
                    cells.insert(cell_addr, new_val);
                    
                    idx += 4 + l;
                }
                
                activation_map.insert(id, activations.len());
                activations.push((id, changes));
            }
            "STOP" => {
                let id: u32 = parts[1].parse().unwrap();
                
                if let Some(idx) = activation_map.remove(&id) {
                    let (_, changes) = activations.remove(idx);
                    activation_map.clear();
                    for (i, (aid, _)) in activations.iter().enumerate() {
                        activation_map.insert(*aid, i);
                    }
                    
                    for (cell_addr, old_val) in changes.iter().rev() {
                        if let Some(val) = old_val {
                            cells.insert(*cell_addr, *val);
                        } else {
                            cells.remove(cell_addr);
                        }
                    }
                }
            }
            "STOPALL" => {
                while !activations.is_empty() {
                    let (_, changes) = activations.pop().unwrap();
                    for (cell_addr, old_val) in changes.iter().rev() {
                        if let Some(val) = old_val {
                            cells.insert(*cell_addr, *val);
                        } else {
                            cells.remove(cell_addr);
                        }
                    }
                }
                activation_map.clear();
            }
            "GET" => {
                let root: i64 = parts[1].parse().unwrap();
                let l: usize = parts[2].parse().unwrap();
                
                let mut current_obj = root;
                let attributes: Vec<i64> = (0..l)
                    .map(|i| parts[3 + i].parse().unwrap())
                    .collect();
                
                for i in 0..(l - 1) {
                    let attr = attributes[i];
                    let (_, obj_ref) = cells.get(&(current_obj, attr)).unwrap();
                    current_obj = *obj_ref;
                }
                
                let target_attr = attributes[l - 1];
                let (is_int, val) = cells.get(&(current_obj, target_attr)).unwrap();
                println!("{} {}", if *is_int { "I" } else { "O" }, val);
            }
            "STACK" => {
                print!("{}", activations.len());
                for (id, _) in &activations {
                    print!(" {}", id);
                }
                println!();
            }
            _ => {}
        }
    }
}