def gen(rng, scale):
    def module_id():
        """Generate [a-z][a-z0-9_]*"""
        c = rng.choice('abcdefghijklmnopqrstuvwxyz')
        return c + ''.join(rng.choices('abcdefghijklmnopqrstuvwxyz0123456789_', k=rng.randint(0, 2)))
    
    def type_terminal():
        """Generate [A-Z][A-Za-z0-9_]*"""
        c = rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        return c + ''.join(rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_', k=rng.randint(0, 2)))
    
    def fv_terminal():
        """Generate [a-z][A-Za-z0-9_]*"""
        c = rng.choice('abcdefghijklmnopqrstuvwxyz')
        return c + ''.join(rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_', k=rng.randint(0, 2)))
    
    def qname(is_type):
        """Generate qualified name: [module.]*terminal"""
        mods = [module_id() for _ in range(rng.randint(0, 2))]
        term = type_terminal() if is_type else fv_terminal()
        return '.'.join(mods + [term]) if mods else term
    
    def context():
        """Generate context: empty or [module.]*"""
        mods = [module_id() for _ in range(rng.randint(0, 2))]
        return '.'.join(mods) if mods else ""
    
    def hash_val():
        return f"h{rng.randint(10000, 99999)}"
    
    if scale == "edge":
        cases = [
            ([], [], []),
            ([("type", "T", None, hash_val())], [], [("type", "T", "", None, None, 0)]),
            ([("function", "f", 0, hash_val())], [], [("function", "f@0", "", None, None, 0)]),
            ([("value", "x", 1, hash_val())], [], [("value", "x@1", "", None, None, 0)]),
            ([], [], [("type", "t", "", None, None, 0)]),
            ([], [], [("function", "F", "", None, None, 0)]),
            ([("type", "A", None, hash_val())], [], [("type", "B", "", None, None, 0)]),
            ([("type", "pkg.T", None, hash_val())], [], [("type", "T", "pkg", None, None, 0)]),
        ]
        return rng.choice(cases)
    
    elif scale == "small":
        initial = []
        
        for _ in range(rng.randint(2, 4)):
            initial.append(("type", qname(True), None, hash_val()))
        
        for _ in range(rng.randint(2, 4)):
            initial.append(("function", qname(False), rng.randint(0, 1), hash_val()))
        
        for _ in range(rng.randint(2, 4)):
            initial.append(("value", qname(False), rng.randint(0, 1), hash_val()))
        
        references = []
        for entry in initial[:7]:
            ns, name, version, _ = entry
            terminal = name.split('.')[-1]
            text = f"{terminal}@{version}" if version is not None else terminal
            refs_context = rng.choice(["", context()])
            references.append((ns, text, refs_context, None, None, 0))
        
        return (initial, [], references)
    
    else:  # medium
        initial = []
        
        for _ in range(rng.randint(7, 14)):
            ns = rng.choice(["type", "function", "value"])
            version = None if ns == "type" else rng.randint(0, 2)
            initial.append((ns, qname(ns == "type"), version, hash_val()))
        
        references = []
        for _ in range(rng.randint(10, 20)):
            if rng.random() < 0.65 and initial:
                entry = rng.choice(initial)
                ns, name, version, _ = entry
                terminal = name.split('.')[-1]
                text = f"{terminal}@{version}" if version is not None else terminal
                refs_context = context()
            else:
                ns = rng.choice(["type", "function", "value"])
                if ns == "type":
                    text = type_terminal()
                else:
                    text = fv_terminal()
                    if rng.random() > 0.55:
                        text = f"{text}@{rng.randint(0, 2)}"
                refs_context = context()
            
            references.append((ns, text, refs_context, None, None, 0))
        
        return (initial, [], references)