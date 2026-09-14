import random

def gen(rng, scale):
    if scale == "edge":
        cases = [
            # Empty ranges and edits
            [[], [], 10, 10],
            # Single range, no edits
            [[(1, 1, 1, 1)], [], 10, 10],
            # Full grid as single range
            [[(1, 1, 10, 10)], [], 10, 10],
            # Single range, insert before it
            [[(5, 5, 10, 10)], [("row", 5, 1)], 20, 20],
            # Single range, insert past it
            [[(5, 5, 10, 10)], [("row", 15, 2)], 20, 20],
            # Single range, column insert
            [[(5, 5, 10, 10)], [("column", 15, 3)], 20, 20],
            # Single range, delete before
            [[(5, 5, 10, 10)], [("row", 1, -2)], 20, 20],
            # Single range, delete overlapping
            [[(5, 5, 10, 10)], [("row", 5, -2)], 20, 20],
            # Single range, delete entire range
            [[(5, 5, 10, 10)], [("row", 5, -6)], 20, 20],
            # Single range, delete after
            [[(5, 5, 10, 10)], [("row", 15, -2)], 20, 20],
            # Overlapping ranges
            [[(1, 1, 5, 5), (3, 3, 7, 7)], [], 10, 10],
            # Touching ranges
            [[(1, 1, 5, 5), (6, 6, 10, 10)], [], 10, 10],
            # Duplicate ranges
            [[(1, 1, 5, 5), (1, 1, 5, 5)], [], 10, 10],
            # Large coordinates
            [[(1, 1, 10**6, 10**6)], [], 10**6 + 1, 10**6 + 1],
            # Multiple mixed edits
            [[(5, 5, 15, 15)], [("row", 10, 2), ("column", 8, -1), ("row", 5, -1)], 30, 30],
            # No ranges, multiple edits
            [[], [("row", 5, 2), ("column", 3, -1)], 30, 30],
            # Edge deletion at start
            [[(1, 1, 5, 5)], [("row", 1, -1)], 10, 10],
            # Edge insertion at start
            [[(5, 5, 10, 10)], [("row", 1, 1)], 20, 20],
        ]
        return rng.choice(cases)
    
    elif scale == "small":
        max_row = rng.randint(10, 100)
        max_col = rng.randint(10, 100)
        
        num_ranges = rng.randint(0, 5)
        ranges = []
        for _ in range(num_ranges):
            r1 = rng.randint(1, max_row)
            c1 = rng.randint(1, max_col)
            r2 = rng.randint(r1, max_row)
            c2 = rng.randint(c1, max_col)
            ranges.append((r1, c1, r2, c2))
        
        edits = []
        num_edits = rng.randint(0, 5)
        for _ in range(num_edits):
            axis = rng.choice(["row", "column"])
            if axis == "row":
                index = rng.randint(1, max_row)
                if rng.random() < 0.6:
                    delta = rng.randint(1, 3)
                else:
                    max_delete = max_row - index + 1
                    d = rng.randint(1, min(2, max_delete))
                    delta = -d
            else:
                index = rng.randint(1, max_col)
                if rng.random() < 0.6:
                    delta = rng.randint(1, 3)
                else:
                    max_delete = max_col - index + 1
                    d = rng.randint(1, min(2, max_delete))
                    delta = -d
            edits.append((axis, index, delta))
        
        return [ranges, edits, max_row, max_col]
    
    elif scale == "medium":
        max_row = rng.randint(100, 500)
        max_col = rng.randint(100, 500)
        
        num_ranges = rng.randint(5, 25)
        ranges = []
        for _ in range(num_ranges):
            r1 = rng.randint(1, max_row)
            c1 = rng.randint(1, max_col)
            r2 = rng.randint(r1, max_row)
            c2 = rng.randint(c1, max_col)
            ranges.append((r1, c1, r2, c2))
        
        edits = []
        num_edits = rng.randint(3, 15)
        for _ in range(num_edits):
            axis = rng.choice(["row", "column"])
            if axis == "row":
                index = rng.randint(1, max_row)
                if rng.random() < 0.6:
                    delta = rng.randint(1, 5)
                else:
                    max_delete = max_row - index + 1
                    d = rng.randint(1, min(4, max_delete))
                    delta = -d
            else:
                index = rng.randint(1, max_col)
                if rng.random() < 0.6:
                    delta = rng.randint(1, 5)
                else:
                    max_delete = max_col - index + 1
                    d = rng.randint(1, min(4, max_delete))
                    delta = -d
            edits.append((axis, index, delta))
        
        return [ranges, edits, max_row, max_col]