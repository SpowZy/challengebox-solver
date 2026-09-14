def gen(rng, scale):
    if scale == "edge":
        return [[], [], []]
    
    elif scale == "small":
        initial = [
            {
                "namespace": "type",
                "name": "TypeA",
                "version": None,
                "hash": "h1"
            },
            {
                "namespace": "function",
                "name": "funcB",
                "version": None,
                "hash": "h2"
            },
            {
                "namespace": "value",
                "name": "valC",
                "version": 1,
                "hash": "h3"
            }
        ]
        
        snapshots = [
            [
                {
                    "namespace": "value",
                    "name": "valD",
                    "version": 2,
                    "hash": "h4"
                }
            ],
            [
                {
                    "namespace": "function",
                    "name": "funcE",
                    "version": None,
                    "hash": "h5"
                }
            ]
        ]
        
        references = [
            {
                "namespace": "type",
                "text": "TypeA",
                "context": "",
                "location": "loc1",
                "hash": "h1",
                "start": 0
            },
            {
                "namespace": "function",
                "text": "funcB",
                "context": "",
                "location": None,
                "hash": None,
                "start": 0
            },
            {
                "namespace": "value",
                "text": "valC@1",
                "context": "",
                "location": None,
                "hash": None,
                "start": 1
            }
        ]
        
        return [initial, snapshots, references]
    
    else:  # medium
        initial = []
        for i in range(40):
            if i < 12:
                ns = "type"
                name = f"Typ{i}"
                ver = None
            elif i < 26:
                ns = "function"
                name = f"fn{i}"
                ver = None if i % 3 == 0 else (1 if i % 3 == 1 else 2)
            else:
                ns = "value"
                name = f"v{i}"
                ver = None if i % 4 == 0 else (1 if i % 4 < 2 else 3)
            
            initial.append({
                "namespace": ns,
                "name": name,
                "version": ver,
                "hash": f"ih{i}"
            })
        
        snapshots = []
        for s in range(12):
            batch = []
            for j in range(5):
                idx = s * 5 + j
                if (s + j) % 3 == 0:
                    ns = "type"
                    name = f"NewT{s}_{j}"
                    ver = None
                elif (s + j) % 3 == 1:
                    ns = "function"
                    name = f"newf{s}_{j}"
                    ver = 1 if idx % 2 else None
                else:
                    ns = "value"
                    name = f"newv{s}_{j}"
                    ver = 2 if idx % 2 else 1
                
                batch.append({
                    "namespace": ns,
                    "name": name,
                    "version": ver,
                    "hash": f"sh{s}_{j}"
                })
            snapshots.append(batch)
        
        references = []
        for i in range(28):
            r = i % 9
            
            if r < 3:
                ns = "type"
                text = f"Typ{i % 12}"
            elif r < 6:
                ns = "function"
                text = f"fn{i % 14}"
                if i % 4 == 0:
                    text += f"@{i % 5}"
            else:
                ns = "value"
                text = f"v{i % 14}"
                if i % 5 == 0:
                    text += f"@{(i // 5) % 4}"
            
            has_location = (i % 4) < 2
            start = rng.randint(0, len(snapshots))
            
            references.append({
                "namespace": ns,
                "text": text,
                "context": "",
                "location": f"l{i}" if has_location else None,
                "hash": f"rh{i}" if has_location else None,
                "start": start
            })
        
        return [initial, snapshots, references]