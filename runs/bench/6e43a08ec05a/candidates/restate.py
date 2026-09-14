def normalize_protection(ranges, edits, max_row, max_col):
    protected = list(ranges)
    
    for axis, index, delta in edits:
        new_protected = []
        
        if axis == "row":
            if delta > 0:
                for r1, c1, r2, c2 in protected:
                    if r2 < index:
                        new_protected.append((r1, c1, r2, c2))
                    elif r1 >= index:
                        new_protected.append((r1 + delta, c1, r2 + delta, c2))
                    else:
                        new_protected.append((r1, c1, index - 1, c2))
                        new_protected.append((index + delta, c1, r2 + delta, c2))
            else:
                d = -delta
                deletion_end = index + d - 1
                for r1, c1, r2, c2 in protected:
                    if r2 < index:
                        new_protected.append((r1, c1, r2, c2))
                    elif r1 > deletion_end:
                        new_protected.append((r1 - d, c1, r2 - d, c2))
                    else:
                        if r1 < index:
                            new_protected.append((r1, c1, index - 1, c2))
                        if r2 > deletion_end:
                            new_protected.append((deletion_end + 1 - d, c1, r2 - d, c2))
        else:
            if delta > 0:
                for r1, c1, r2, c2 in protected:
                    if c2 < index:
                        new_protected.append((r1, c1, r2, c2))
                    elif c1 >= index:
                        new_protected.append((r1, c1 + delta, r2, c2 + delta))
                    else:
                        new_protected.append((r1, c1, r2, index - 1))
                        new_protected.append((r1, index + delta, r2, c2 + delta))
            else:
                d = -delta
                deletion_end = index + d - 1
                for r1, c1, r2, c2 in protected:
                    if c2 < index:
                        new_protected.append((r1, c1, r2, c2))
                    elif c1 > deletion_end:
                        new_protected.append((r1, c1 - d, r2, c2 - d))
                    else:
                        if c1 < index:
                            new_protected.append((r1, c1, r2, index - 1))
                        if c2 > deletion_end:
                            new_protected.append((r1, deletion_end + 1 - d, r2, c2 - d))
        
        protected = new_protected
    
    if not protected:
        return []
    
    row_boundaries = set()
    for r1, c1, r2, c2 in protected:
        row_boundaries.add(r1)
        row_boundaries.add(r2 + 1)
    row_boundaries = sorted(row_boundaries)
    
    segments = []
    for i in range(len(row_boundaries) - 1):
        row_start = row_boundaries[i]
        row_end = row_boundaries[i + 1] - 1
        
        intervals = []
        for r1, c1, r2, c2 in protected:
            if r1 <= row_start and row_end <= r2:
                intervals.append((c1, c2))
        
        if intervals:
            intervals.sort()
            merged = []
            for c1, c2 in intervals:
                if merged and c1 <= merged[-1][1] + 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
                else:
                    merged.append((c1, c2))
            segments.append((row_start, row_end, tuple(merged)))
    
    result = []
    if segments:
        i = 0
        while i < len(segments):
            row_start, row_end, intervals = segments[i]
            j = i
            
            while j + 1 < len(segments) and segments[j + 1][0] == row_end + 1 and segments[j + 1][2] == intervals:
                _, row_end, _ = segments[j + 1]
                j += 1
            
            for c1, c2 in intervals:
                result.append((row_start, c1, row_end, c2))
            
            i = j + 1
    
    result.sort()
    return result