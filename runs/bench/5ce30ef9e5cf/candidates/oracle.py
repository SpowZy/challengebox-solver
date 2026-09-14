def main():
    n, k, q = map(int, input().split())
    
    cells = {}
    for _ in range(k):
        parts = input().split()
        obj = int(parts[0])
        attr = int(parts[1])
        kind = parts[2]
        value = int(parts[3])
        if obj not in cells:
            cells[obj] = {}
        cells[obj][attr] = (kind, value)
    
    activation_order = []
    activation_remembered = {}
    
    def resolve_path(root, attributes):
        current_obj = root
        for attr in attributes[:-1]:
            kind, value = cells[current_obj][attr]
            current_obj = value
        return (current_obj, attributes[-1])
    
    def get_cell_value(cell):
        obj, attr = cell
        return cells[obj][attr]
    
    def set_cell_value(cell, kind, value):
        obj, attr = cell
        if obj not in cells:
            cells[obj] = {}
        cells[obj][attr] = (kind, value)
    
    for _ in range(q):
        line = input().split()
        cmd = line[0]
        
        if cmd == "START":
            act_id = int(line[1])
            m = int(line[2])
            idx = 3
            remembered = []
            for _ in range(m):
                root = int(line[idx])
                l = int(line[idx + 1])
                attributes = [int(line[idx + 2 + i]) for i in range(l)]
                kind = line[idx + 2 + l]
                value = int(line[idx + 3 + l])
                
                cell = resolve_path(root, attributes)
                remembered.append((cell, get_cell_value(cell)))
                set_cell_value(cell, kind, value)
                
                idx += 4 + l
            
            activation_order.append(act_id)
            activation_remembered[act_id] = remembered
        
        elif cmd == "STOP":
            act_id = int(line[1])
            if act_id in activation_remembered:
                for cell, (kind, value) in reversed(activation_remembered[act_id]):
                    set_cell_value(cell, kind, value)
                activation_order.remove(act_id)
                del activation_remembered[act_id]
        
        elif cmd == "STOPALL":
            while activation_order:
                act_id = activation_order[-1]
                for cell, (kind, value) in reversed(activation_remembered[act_id]):
                    set_cell_value(cell, kind, value)
                activation_order.pop()
                del activation_remembered[act_id]
        
        elif cmd == "GET":
            root = int(line[1])
            l = int(line[2])
            attributes = [int(line[3 + i]) for i in range(l)]
            cell = resolve_path(root, attributes)
            kind, value = get_cell_value(cell)
            print(f"{kind} {value}")
        
        elif cmd == "STACK":
            print(len(activation_order), *activation_order)

if __name__ == "__main__":
    main()