import sys

line = sys.stdin.readline().strip()
N, K, Q = map(int, line.split())

cells = {}

for _ in range(K):
    parts = sys.stdin.readline().strip().split()
    obj = int(parts[0])
    attr = int(parts[1])
    kind = parts[2]
    value = int(parts[3])
    cells[(obj, attr)] = (kind, value)

active = {}
active_order = []

def resolve_path(root, path_attrs):
    current_obj = root
    for i in range(len(path_attrs) - 1):
        attr = path_attrs[i]
        kind, value = cells[(current_obj, attr)]
        current_obj = value
    return (current_obj, path_attrs[-1])

def execute_start(activation_id, replacements):
    remembered = []
    for root, path_attrs, kind, value in replacements:
        obj, attr = resolve_path(root, path_attrs)
        old_state = cells.get((obj, attr))
        remembered.append(((obj, attr), old_state))
        cells[(obj, attr)] = (kind, value)
    
    active[activation_id] = remembered
    active_order.append(activation_id)

def execute_stop(activation_id):
    if activation_id not in active:
        return
    
    remembered = active[activation_id]
    for (obj, attr), old_state in reversed(remembered):
        if old_state is None:
            if (obj, attr) in cells:
                del cells[(obj, attr)]
        else:
            cells[(obj, attr)] = old_state
    
    del active[activation_id]
    active_order.remove(activation_id)

def execute_stopall():
    while active_order:
        activation_id = active_order[-1]
        execute_stop(activation_id)

def execute_get(root, path_attrs):
    obj, attr = resolve_path(root, path_attrs)
    kind, value = cells[(obj, attr)]
    print(f"{kind} {value}")

def execute_stack():
    output = [str(len(active_order))]
    output.extend(map(str, active_order))
    print(' '.join(output))

for _ in range(Q):
    line = sys.stdin.readline().strip()
    parts = line.split()
    
    if parts[0] == 'START':
        activation_id = int(parts[1])
        M = int(parts[2])
        replacements = []
        
        idx = 3
        for _ in range(M):
            root = int(parts[idx])
            L = int(parts[idx + 1])
            path_attrs = [int(parts[idx + 2 + i]) for i in range(L)]
            kind = parts[idx + 2 + L]
            value = int(parts[idx + 3 + L])
            replacements.append((root, path_attrs, kind, value))
            idx += 4 + L
        
        execute_start(activation_id, replacements)
    
    elif parts[0] == 'STOP':
        activation_id = int(parts[1])
        execute_stop(activation_id)
    
    elif parts[0] == 'STOPALL':
        execute_stopall()
    
    elif parts[0] == 'GET':
        root = int(parts[1])
        L = int(parts[2])
        path_attrs = [int(parts[3 + i]) for i in range(L)]
        execute_get(root, path_attrs)
    
    elif parts[0] == 'STACK':
        execute_stack()