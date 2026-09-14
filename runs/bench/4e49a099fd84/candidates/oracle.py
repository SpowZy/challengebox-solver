import sys

def is_control(s):
    return (0 <= s <= 0x1F) or (0x7F <= s <= 0x9F)

def is_attachment(s):
    ranges = [(0x0300, 0x036F), (0x1AB0, 0x1AFF), (0x1DC0, 0x1DFF), 
              (0x20D0, 0x20FF), (0xFE00, 0xFE0F), (0xFE20, 0xFE2F),
              (0x1F3FB, 0x1F3FF), (0xE0100, 0xE01EF)]
    for lo, hi in ranges:
        if lo <= s <= hi:
            return True
    return False

def is_emoji(s):
    return (0x2600 <= s <= 0x27BF) or (0x1F000 <= s <= 0x1FAFF)

def is_regional(s):
    return 0x1F1E6 <= s <= 0x1F1FF

def read_scalars(s):
    r = []
    i = 0
    while i < len(s):
        b = ord(s[i])
        if b < 0x80:
            r.append(b)
            i += 1
        elif b < 0xE0:
            r.append(((b & 0x1F) << 6) | (ord(s[i+1]) & 0x3F))
            i += 2
        elif b < 0xF0:
            r.append(((b & 0x0F) << 12) | ((ord(s[i+1]) & 0x3F) << 6) | (ord(s[i+2]) & 0x3F))
            i += 3
        else:
            r.append(((b & 0x07) << 18) | ((ord(s[i+1]) & 0x3F) << 12) | ((ord(s[i+2]) & 0x3F) << 6) | (ord(s[i+3]) & 0x3F))
            i += 4
    return r

def boundary_after(sc, i):
    if i >= len(sc) - 1:
        return True
    l, r = sc[i], sc[i+1]
    
    if l == 0x0D and r == 0x0A:
        return False
    if is_control(l) or is_control(r):
        return True
    if is_attachment(r) or r == 0x200D:
        return False
    if l == 0x200D and is_emoji(r):
        j = i - 1
        while j >= 0 and is_attachment(sc[j]):
            j -= 1
        if j >= 0 and is_emoji(sc[j]):
            return False
    if is_regional(l) and is_regional(r):
        c = 1
        j = i - 1
        while j >= 0 and is_regional(sc[j]):
            c += 1
            j -= 1
        return c % 2 == 0
    return True

def write_scalar(sc):
    b = []
    for s in sc:
        if s < 0x80:
            b.append(chr(s))
        elif s < 0x800:
            b.append(chr(0xC0 | (s >> 6)))
            b.append(chr(0x80 | (s & 0x3F)))
        elif s < 0x10000:
            b.append(chr(0xE0 | (s >> 12)))
            b.append(chr(0x80 | ((s >> 6) & 0x3F)))
            b.append(chr(0x80 | (s & 0x3F)))
        else:
            b.append(chr(0xF0 | (s >> 18)))
            b.append(chr(0x80 | ((s >> 12) & 0x3F)))
            b.append(chr(0x80 | ((s >> 6) & 0x3F)))
            b.append(chr(0x80 | (s & 0x3F)))
    return ''.join(b)

def utf16_len(s):
    return 1 if s <= 0xFFFF else 2

t = sys.stdin.read().split()
S = t[0]
Q = int(t[1])

sc = read_scalars(S)

g = []
curr = []
for i in range(len(sc)):
    curr.append(sc[i])
    if i == len(sc) - 1 or boundary_after(sc, i):
        g.append(curr)
        curr = []

u16 = [0]
for grapheme in g:
    u16.append(u16[-1] + sum(utf16_len(x) for x in grapheme))

N = len(g)

for idx in range(Q):
    qt = int(t[2 + idx * 3])
    a = int(t[2 + idx * 3 + 1])
    b = int(t[2 + idx * 3 + 2])
    
    if a < 0:
        a = N + a
    a = max(0, min(a, N))
    if b < 0:
        b = N + b
    b = max(0, min(b, N))
    
    if qt == 1:
        if b < a:
            print(f"{u16[a]} {u16[a]}")
        else:
            print(f"{u16[a]} {u16[b]}")
    else:
        L = 0
        if a < N and b < N:
            m = min(N - a, N - b)
            for k in range(m):
                if write_scalar(g[a+k]) == write_scalar(g[b+k]):
                    L += 1
                else:
                    break
        w = u16[a+L] - u16[a]
        print(f"{L} {w}")