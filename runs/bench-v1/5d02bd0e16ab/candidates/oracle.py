def main():
    line = input().split()
    N = int(line[0])
    Q = int(line[1])
    
    versions = [
        {
            'p': 0,
            'c': 0,
            'd': 0,
            'tickets': [None] * N,
            'published': {},
        }
    ]
    
    for _ in range(Q):
        parts = input().split()
        op = parts[0]
        b = int(parts[1])
        
        prev = versions[b]
        new_state = {
            'p': prev['p'],
            'c': prev['c'],
            'd': prev['d'],
            'tickets': list(prev['tickets']),
            'published': dict(prev['published']),
        }
        
        if op == 'R':
            s = int(parts[2])
            new_state['tickets'][s - 1] = new_state['p']
            new_state['p'] += 1
        
        elif op == 'W':
            s = int(parts[2])
            ticket = new_state['tickets'][s - 1]
            if parts[3] == 'E':
                new_state['published'][ticket] = None
            else:
                x = int(parts[4])
                new_state['published'][ticket] = x
        
        elif op == 'D':
            k = int(parts[2])
            new_state['d'] += k
        
        elif op == 'P':
            m = 0
            h = 0
            c = new_state['c']
            d = new_state['d']
            p = new_state['p']
            
            while c < p:
                if c not in new_state['published']:
                    break
                
                value = new_state['published'][c]
                if value is None:
                    c += 1
                else:
                    if d == 0:
                        break
                    m += 1
                    r = value % 1000000007
                    h = (h * 911382323 + r) % 1000000007
                    c += 1
                    d -= 1
            
            new_state['c'] = c
            new_state['d'] = d
            
            if p == c == N:
                status = 'COMPLETE'
            elif c == p < N:
                status = 'WAITING'
            elif c < p and c not in new_state['published']:
                status = 'BLOCKED'
            elif c < p and new_state['published'][c] is not None and d == 0:
                status = 'BACKPRESSURE'
            
            print(f'DRAIN {m} {h} {status} {p} {c} {d}')
        
        versions.append(new_state)

if __name__ == '__main__':
    main()