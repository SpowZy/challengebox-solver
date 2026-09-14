def validate_build(schemas, root, operations):
    def get_schema_size(s_idx, memo=None):
        if memo is None:
            memo = {}
        if s_idx in memo:
            return memo[s_idx]
        schema = schemas[s_idx]
        size = 0
        for term in schema:
            if term[0] == "field":
                size += 1
            elif term[0] == "repeat":
                _, t, r = term
                sub_size = get_schema_size(t, memo)
                size += r * sub_size
        memo[s_idx] = size
        return size

    def schema_all_primitive(s_idx, memo=None):
        if memo is None:
            memo = {}
        if s_idx in memo:
            return memo[s_idx]
        schema = schemas[s_idx]
        for term in schema:
            if term[0] == "field":
                _, _, desc = term
                if desc not in ["int", "text"]:
                    memo[s_idx] = False
                    return False
            elif term[0] == "repeat":
                _, t, r = term
                if not schema_all_primitive(t, memo):
                    memo[s_idx] = False
                    return False
        memo[s_idx] = True
        return True

    memo_size = {}
    memo_prim = {}

    def get_field(s_idx, field_idx):
        schema = schemas[s_idx]
        current_idx = 0
        for term in schema:
            if term[0] == "field":
                if current_idx == field_idx:
                    _, name, d = term
                    return name, d
                current_idx += 1
            elif term[0] == "repeat":
                _, t, r = term
                sub_size = get_schema_size(t, memo_size)
                total_size = r * sub_size
                if field_idx < current_idx + total_size:
                    relative_idx = (field_idx - current_idx) % sub_size
                    return get_field(t, relative_idx)
                current_idx += total_size
        return None

    root_size = get_schema_size(root, memo_size)
    container_stack = [("record", (root, root_size), 0)]

    for op_idx, op in enumerate(operations, 1):
        if not container_stack:
            return op_idx
        container_type, container_info, pos = container_stack[-1]

        if op[0] == "put":
            _, name, p = op
            if container_type == "record":
                s_idx, size = container_info
                if pos >= size:
                    return op_idx
                field_result = get_field(s_idx, pos)
                if field_result is None or field_result[0] != name or field_result[1] != p:
                    return op_idx
                container_stack[-1] = ("record", container_info, pos + 1)
            else:
                element_desc, capacity = container_info
                if name is not None or pos >= capacity or element_desc != p:
                    return op_idx
                container_stack[-1] = ("array", container_info, pos + 1)

        elif op[0] == "open":
            _, name, d = op
            if container_type == "record":
                s_idx, size = container_info
                if pos >= size:
                    return op_idx
                field_result = get_field(s_idx, pos)
                if field_result is None or field_result[0] != name or field_result[1] != d:
                    return op_idx
                container_stack[-1] = ("record", container_info, pos + 1)
                if d[0] == "record":
                    new_size = get_schema_size(d[1], memo_size)
                    container_stack.append(("record", (d[1], new_size), 0))
                else:
                    container_stack.append(("array", (d[1], d[2]), 0))
            else:
                element_desc, capacity = container_info
                if name is not None or pos >= capacity or element_desc != d:
                    return op_idx
                container_stack[-1] = ("array", container_info, pos + 1)
                if d[0] == "record":
                    new_size = get_schema_size(d[1], memo_size)
                    container_stack.append(("record", (d[1], new_size), 0))
                else:
                    container_stack.append(("array", (d[1], d[2]), 0))

        elif op[0] == "default":
            _, k = op
            if container_type == "record":
                s_idx, size = container_info
                if pos + k > size:
                    return op_idx
                check_limit = min(k, 1000)
                for i in range(check_limit):
                    field_result = get_field(s_idx, pos + i)
                    if field_result is None or field_result[1] not in ["int", "text"]:
                        return op_idx
                if k > 1000 and not schema_all_primitive(s_idx, memo_prim):
                    return op_idx
                container_stack[-1] = ("record", container_info, pos + k)
            else:
                element_desc, capacity = container_info
                if element_desc not in ["int", "text"] or pos + k > capacity:
                    return op_idx
                container_stack[-1] = ("array", container_info, pos + k)

        elif op[0] == "close":
            if container_type == "record":
                s_idx, size = container_info
                if pos != size:
                    return op_idx
            container_stack.pop()

    return 0 if len(container_stack) == 0 else len(operations) + 1