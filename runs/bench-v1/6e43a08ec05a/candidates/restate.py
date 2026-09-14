def normalize_protection(ranges, edits, max_row, max_col):
    rects = list(ranges)
    
    for axis, index, delta in edits:
        new_rects = []
        for r1, c1, r2, c2 in rects:
            if axis == "row":
                if delta > 0:
                    transformed = _transform_rect_row_insert(r1, c1, r2, c2, index, delta, max_row)
                else:
                    transformed = _transform_rect_row_delete(r1, c1, r2, c2, index, -delta, max_row)
            else:
                if delta > 0:
                    transformed = _transform_rect_col_insert(r1, c1, r2, c2, index, delta, max_col)
                else:
                    transformed = _transform_rect_col_delete(r1, c1, r2, c2, index, -delta, max_col)
            new_rects.extend(transformed)
        rects = new_rects
    
    rects = [(r1, c1, r2, c2) for r1, c1, r2, c2 in rects if r1 <= r2 and c1 <= c2]
    
    if not rects:
        return []
    
    critical_rows = set()
    for r1, c1, r2, c2 in rects:
        critical_rows.add(r1)
        critical_rows.add(r2 + 1)
    
    critical_rows = sorted(critical_rows)
    result = []
    
    for i, r in enumerate(critical_rows):
        if r > max_row:
            break
        
        col_intervals = []
        for r1, c1, r2, c2 in rects:
            if r1 <= r <= r2:
                col_intervals.append((c1, c2))
        
        if not col_intervals:
            continue
        
        col_intervals.sort()
        merged = []
        for c1, c2 in col_intervals:
            if merged and merged[-1][1] >= c1 - 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
            else:
                merged.append((c1, c2))
        
        end_r = min(critical_rows[i + 1] - 1, max_row) if i + 1 < len(critical_rows) else max_row
        
        for c1, c2 in merged:
            result.append((r, c1, end_r, c2))
    
    result.sort()
    return result


def _transform_rect_row_insert(r1, c1, r2, c2, index, delta, max_row):
    if r2 < index:
        return [(r1, c1, r2, c2)]
    elif r1 >= index:
        new_r1 = r1 + delta
        new_r2 = r2 + delta
        return [(new_r1, c1, min(new_r2, max_row), c2)] if new_r1 <= max_row else []
    else:
        result = [(r1, c1, index - 1, c2)]
        new_r1 = index + delta
        new_r2 = r2 + delta
        if new_r1 <= max_row:
            result.append((new_r1, c1, min(new_r2, max_row), c2))
        return result


def _transform_rect_row_delete(r1, c1, r2, c2, index, d, max_row):
    if r2 < index:
        return [(r1, c1, r2, c2)]
    elif r1 >= index + d:
        return [(r1 - d, c1, r2 - d, c2)]
    else:
        result = []
        if r1 < index:
            result.append((r1, c1, min(r2, index - 1), c2))
        if r2 >= index + d:
            result.append((max(r1, index + d) - d, c1, r2 - d, c2))
        return result


def _transform_rect_col_insert(r1, c1, r2, c2, index, delta, max_col):
    if c2 < index:
        return [(r1, c1, r2, c2)]
    elif c1 >= index:
        new_c1 = c1 + delta
        new_c2 = c2 + delta
        return [(r1, new_c1, r2, min(new_c2, max_col))] if new_c1 <= max_col else []
    else:
        result = [(r1, c1, r2, index - 1)]
        new_c1 = index + delta
        new_c2 = c2 + delta
        if new_c1 <= max_col:
            result.append((r1, new_c1, r2, min(new_c2, max_col)))
        return result


def _transform_rect_col_delete(r1, c1, r2, c2, index, d, max_col):
    if c2 < index:
        return [(r1, c1, r2, c2)]
    elif c1 >= index + d:
        return [(r1, c1 - d, r2, c2 - d)]
    else:
        result = []
        if c1 < index:
            result.append((r1, c1, r2, min(c2, index - 1)))
        if c2 >= index + d:
            result.append((r1, max(c1, index + d) - d, r2, c2 - d))
        return result