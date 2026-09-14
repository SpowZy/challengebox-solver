use std::io::{self, BufRead};
use std::collections::HashMap;

#[derive(Clone)]
enum CellValue {
    Integer(i64),
    ObjectRef(i64),
}

struct Patchboard {
    cells: HashMap<(i64, i64), CellValue>,
    active_activations: Vec<i64>,
    activation_memories: HashMap<i64, Vec<((i64, i64), CellValue)>>,
}

impl Patchboard {
    fn new() -> Self {
        Patchboard {
            cells: HashMap::new(),
            active_activations: Vec::new(),
            activation_memories: HashMap::new(),
        }
    }
    
    fn resolve_path(&self, root: i64, attrs: &[i64]) -> (i64, i64) {
        let mut current = root;
        for i in 0..attrs.len()-1 {
            let attr = attrs[i];
            if let Some(CellValue::ObjectRef(obj)) = self.cells.get(&(current, attr)) {
                current = *obj;
            }
        }
        (current, attrs[attrs.len()-1])
    }
    
    fn start(&mut self, id: i64, replacements: Vec<(i64, Vec<i64>, CellValue)>) {
        let mut memories = Vec::new();
        
        for (root, attrs, new_value) in replacements {
            let (target_obj, target_attr) = self.resolve_path(root, &attrs);
            let key = (target_obj, target_attr);
            
            let old_value = self.cells.get(&key).cloned().unwrap();
            memories.push((key, old_value));
            self.cells.insert(key, new_value);
        }
        
        self.active_activations.push(id);
        self.activation_memories.insert(id, memories);
    }
    
    fn stop(&mut self, id: i64) {
        if let Some(pos) = self.active_activations.iter().position(|&x| x == id) {
            self.active_activations.remove(pos);
            
            if let Some(memories) = self.activation_memories.remove(&id) {
                for ((obj, attr), old_value) in memories.iter().rev() {
                    self.cells.insert((*obj, *attr), old_value.clone());
                }
            }
        }
    }
    
    fn stopall(&mut self) {
        while !self.active_activations.is_empty() {
            let id = self.active_activations.pop().unwrap();
            if let Some(memories) = self.activation_memories.remove(&id) {
                for ((obj, attr), old_value) in memories.iter().rev() {
                    self.cells.insert((*obj, *attr), old_value.clone());
                }
            }
        }
    }
    
    fn get(&self, root: i64, attrs: &[i64]) -> CellValue {
        let (target_obj, target_attr) = self.resolve_path(root, attrs);
        self.cells.get(&(target_obj, target_attr)).cloned().unwrap()
    }
    
    fn stack(&self) {
        print!("{}", self.active_activations.len());
        for &id in &self.active_activations {
            print!(" {}", id);
        }
        println!();
    }
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    
    let first_line = lines.next().unwrap().unwrap();
    let parts: Vec<&str> = first_line.split_whitespace().collect();
    let k: i64 = parts[1].parse().unwrap();
    let q: i64 = parts[2].parse().unwrap();
    
    let mut patchboard = Patchboard::new();
    
    for _ in 0..k {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        let obj: i64 = parts[0].parse().unwrap();
        let attr: i64 = parts[1].parse().unwrap();
        let value: i64 = parts[3].parse().unwrap();
        
        let cell_value = match parts[2] {
            "I" => CellValue::Integer(value),
            "O" => CellValue::ObjectRef(value),
            _ => panic!(),
        };
        
        patchboard.cells.insert((obj, attr), cell_value);
    }
    
    for _ in 0..q {
        let line = lines.next().unwrap().unwrap();
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        match parts[0] {
            "START" => {
                let id: i64 = parts[1].parse().unwrap();
                let m: usize = parts[2].parse().unwrap();
                
                let mut idx = 3;
                let mut replacements = Vec::new();
                for _ in 0..m {
                    let root: i64 = parts[idx].parse().unwrap();
                    let l: usize = parts[idx+1].parse().unwrap();
                    idx += 2;
                    
                    let mut attrs = Vec::new();
                    for _ in 0..l {
                        attrs.push(parts[idx].parse().unwrap());
                        idx += 1;
                    }
                    
                    let value: i64 = parts[idx+1].parse().unwrap();
                    let cell_value = match parts[idx] {
                        "I" => CellValue::Integer(value),
                        "O" => CellValue::ObjectRef(value),
                        _ => panic!(),
                    };
                    idx += 2;
                    
                    replacements.push((root, attrs, cell_value));
                }
                
                patchboard.start(id, replacements);
            }
            "STOP" => {
                let id: i64 = parts[1].parse().unwrap();
                patchboard.stop(id);
            }
            "STOPALL" => {
                patchboard.stopall();
            }
            "GET" => {
                let root: i64 = parts[1].parse().unwrap();
                let l: usize = parts[2].parse().unwrap();
                let mut attrs = Vec::new();
                for i in 0..l {
                    attrs.push(parts[3+i].parse().unwrap());
                }
                let value = patchboard.get(root, &attrs);
                match value {
                    CellValue::Integer(i) => println!("I {}", i),
                    CellValue::ObjectRef(o) => println!("O {}", o),
                }
            }
            "STACK" => {
                patchboard.stack();
            }
            _ => {}
        }
    }
}