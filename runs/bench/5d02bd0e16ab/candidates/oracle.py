line = input().split()
N = int(line[0])
Q = int(line[1])

versions = {}

versions[0] = {
    'p': 0,
    'c': 0,
    'd': 0,
    'published': [None] * N,
    'tickets': {}
}

for op_idx in range(1, Q + 1):
    parts = input().split()
    op_type = parts[0]
    b = int(parts[1])
    
    prev_state = versions[b]
    current_state = {
        'p': prev_state['p'],
        'c': prev_state['c'],
        'd': prev_state['d'],
        'published': prev_state['published'][:],
        'tickets': prev_state['tickets'].copy()
    }
    
    if op_type == 'R':
        s = int(parts[2])
        current_state['tickets'][s] = current_state['p']
        current_state['p'] += 1
    
    elif op_type == 'W':
        s = int(parts[2])
        if parts[3] == 'E':
            ticket = current_state['tickets'][s]
            current_state['published'][ticket] = 'E'
        else:
            x = int(parts[4])
            ticket = current_state['tickets'][s]
            current_state['published'][ticket] = x
    
    elif op_type == 'D':
        k = int(parts[2])
        current_state['d'] += k
    
    elif op_type == 'P':
        m = 0
        h = 0
        
        while current_state['c'] < current_state['p']:
            slot = current_state['published'][current_state['c']]
            
            if slot is None:
                break
            elif slot == 'E':
                current_state['c'] += 1
            else:
                if current_state['d'] == 0:
                    break
                x = slot
                r = x % 1000000007
                h = (h * 911382323 + r) % 1000000007
                m += 1
                current_state['c'] += 1
                current_state['d'] -= 1
        
        if current_state['p'] == current_state['c'] == N:
            status = 'COMPLETE'
        elif current_state['c'] == current_state['p'] < N:
            status = 'WAITING'
        elif current_state['c'] < current_state['p']:
            slot = current_state['published'][current_state['c']]
            if slot is None:
                status = 'BLOCKED'
            else:
                status = 'BACKPRESSURE'
        
        print(f'DRAIN {m} {h} {status} {current_state["p"]} {current_state["c"]} {current_state["d"]}')
    
    versions[op_idx] = current_state