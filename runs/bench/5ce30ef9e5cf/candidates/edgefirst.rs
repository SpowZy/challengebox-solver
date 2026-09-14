use std::collections::HashMap;
use std::io::BufRead;

fn main() {
    let stdin = std::io::stdin();
    let mut lines = stdin.lock().lines().map(|l| l.unwrap());
    
    let first_line = lines.next().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let _n: i64 = parts[0].parse().unwrap();
    let k: usize = parts[1].parse().unwrap();
    let q: usize = parts[2].parse().unwrap();
    
    #[derive(Clone)]
    enum CellValue {
        I(i64),
        O(i64),
    }
    
    let mut cells: HashMap<(i64, i64), CellValue> = HashMap::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let object: i64 = parts[0].parse().unwrap();
        let attribute: i64 = parts[1].parse().unwrap();
        let kind = parts[2];
        let value: i64 = parts[3].parse().unwrap();
        
        let cell_value = match kind {
            "I" => CellValue::I(value),
            "O" => CellValue::O(value),
            _ => unreachable!(),
        };
        
        cells.insert((object, attribute), cell_value);
    }
    
    let mut active_activations: HashMap<i64, Vec<((i64, i64), CellValue)>> = HashMap::new();
    let mut activation_order: Vec<i64> = Vec::new();
    
    let resolve_path = |root: i64, attrs: &[i64], cells: &HashMap<(i64, i64), CellValue>| -> (i64, i64) {
        let mut current = root;
        for (i, &attr) in attrs.iter().enumerate() {
            if i == attrs.len() - 1 {
                return (current, attr);
            }
            if let Some(CellValue::O(obj)) = cells.get(&(current, attr)) {
                current = *obj;
            }
        }
        unreachable!()
    };
    
    for _ in 0..q {
        let line = lines.next().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let command = parts[0];
        
        if command == "START" {
            let id: i64 = parts[1].parse().unwrap();
            let m: usize = parts[2].parse().unwrap();
            
            let mut idx = 3;
            let mut remembered = Vec::new();
            
            for _ in 0..m {
                let root: i64 = parts[idx].parse().unwrap();
                idx += 1;
                let l: usize = parts[idx].parse().unwrap();
                idx += 1;
                
                let mut attrs = Vec::new();
                for _ in 0..l {
                    attrs.push(parts[idx].parse().unwrap());
                    idx += 1;
                }
                
                let kind = parts[idx];
                idx += 1;
                let value: i64 = parts[idx].parse().unwrap();
                idx += 1;
                
                let cell_value = match kind {
                    "I" => CellValue::I(value),
                    "O" => CellValue::O(value),
                    _ => unreachable!(),
                };
                
                let cell_key = resolve_path(root, &attrs, &cells);
                let old_value = cells.get(&cell_key).unwrap().clone();
                remembered.push((cell_key, old_value));
                cells.insert(cell_key, cell_value);
            }
            
            active_activations.insert(id, remembered);
            activation_order.push(id);
        } else if command == "STOP" {
            let id: i64 = parts[1].parse().unwrap();
            
            if let Some(remembered) = active_activations.remove(&id) {
                for (cell_key, old_value) in remembered.iter().rev() {
                    cells.insert(*cell_key, old_value.clone());
                }
                activation_order.retain(|&x| x != id);
            }
        } else if command == "STOPALL" {
            while let Some(id) = activation_order.pop() {
                if let Some(remembered) = active_activations.remove(&id) {
                    for (cell_key, old_value) in remembered.iter().rev() {
                        cells.insert(*cell_key, old_value.clone());
                    }
                }
            }
        } else if command == "GET" {
            let root: i64 = parts[1].parse().unwrap();
            let l: usize = parts[2].parse().unwrap();
            
            let mut attrs = Vec::new();
            for i in 0..l {
                attrs.push(parts[3 + i].parse().unwrap());
            }
            
            let cell_key = resolve_path(root, &attrs, &cells);
            match cells.get(&cell_key).unwrap() {
                CellValue::I(val) => println!("I {}", val),
                CellValue::O(val) => println!("O {}", val),
            }
        } else if command == "STACK" {
            print!("{}", activation_order.len());
            for &id in &activation_order {
                print!(" {}", id);
            }
            println!();
        }
    }
}