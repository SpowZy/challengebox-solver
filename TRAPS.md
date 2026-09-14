# Traps, per problem

Across 10 statements the trap pass quoted **60 clauses** that change the answer if read the usual way instead of the way they are written. On **8** of them, candidates written from different readings then behaved differently on the same input. That is a disagreement about meaning, not about typing.

typing.

Every disagreement below shows the input that produced it. Regenerate with `python traps_report.py runs/bench -o TRAPS.md`.

**About the quotes.** The trap prompt asks for the clause verbatim, and asking is not checking, so every quote is matched back against the statement it claims to come from and labelled with the result. Of the 60: **31 are literal spans** of the statement, **14** reproduce it in pieces across an elision, and **15** are the model's own wording for a clause rather than the clause. A paraphrase can still point at a real trap, and several here do, but it is not a citation and this file does not call it one. The check is a substring match after whitespace and punctuation are normalised; `locate_quote` in `solver/analyse.py`.

## Why this file exists

Sampling one prompt N times varies the seed. It does not vary the reading, so a misread clause is misread by all N candidates at once and the majority is unanimously wrong. Behavioural clustering removes generation noise and leaves statement misinterpretation untouched. That is the measured residual in [2506.11021](https://arxiv.org/abs/2506.11021), and it is this benchmark's whole difficulty. So the seven candidates are written from seven different reading strategies, and where they split, the split is recorded here rather than voted away.

---

## `1ba0d34fae43`, python, `simulate_writes`

*Simulate a congestion-aware retry mechanism with shared spin-credit tracking and implicit error handling.*

**Stated maximum:** 200k packets; 200k outcome runs with 10^18 counts; level_cap 60; credit_cap 10^30.

**6 traps quoted:**

- **MAGNITUDE**: a bound past the point where the obvious numeric type stops being safe
  > run-length encoded chronological list... run counts are at most `10^18`

  *the model's wording, not the statement's*

  Missing it produces: Expanding runs into an array causes memory/time explosion; algorithm becomes infeasible.

  Required instead: Process outcomes implicitly with run index and offset; never expand run counts.

- **MAGNITUDE**: a bound past the point where the obvious numeric type stops being safe
  > cost = min(2**old_level, spin_limit) where level_cap <= 60

  *the model's wording, not the statement's*

  Missing it produces: Computing 2^59 or overflow produces wrong spin/yield counts without arbitrary precision.

  Required instead: Use full-precision arithmetic; compute 2^old_level directly for all comparisons and sums.

- **COMPLEXITY**: a size at which the obvious approach is a wrong answer
  > After all runs are exhausted, every later attempt implicitly returns `error`.

  *quoted in pieces, across an elision*

  Missing it produces: Retry loops fail to terminate; infinite loops or wrong attempt counts.

  Required instead: Track outcome position; return implicit error when past last run; count these attempts.

- **PRECEDENCE**: numbered rules that must be applied in order, first match winning
  > packet is dropped immediately; that final 'full' causes no spin, yield, or credit deduction

  *quoted in pieces, across an elision*

  Missing it produces: If conditions fail, credits/spins still deducted; level incorrectly reverts for next packets.

  Required instead: Check both conditions before any side effect; drop immediately if either fails; level persists.

- **REDEFINITION**: a standard term redefined to mean something else
  > 'error' fails the packet and resets the level to zero. Credits are unchanged.

  *quoted in pieces, across an elision*

  Missing it produces: Incorrect final credits if they are reset on error instead of persisting.

  Required instead: On error: reset level only; never modify credits. Credits change only on 'ok' or 'full'.

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > retries have already been scheduled for this packet ... max_retries applies per packet

  *the model's wording, not the statement's*

  Missing it produces: Global retry limit applied instead of per-packet; vastly more retries than intended.

  Required instead: Track retry_count per packet; check retry_count < max_retries for each packet independently.

**Verification:** 18 generated inputs, 6 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `==================`: adversarial, edgefirst, literal, plain, restate, traps
- `!!=====!!!=!!!=!=!`: complexity

First divergence, framing `complexity`, case `edge#28539`:

```
input     [[1], [["full", 1]], 1, 10, 1000000000000000000, 1000000000000000000000000000000, 1000000000000000000000000000000]
reference {"packets": [["ERROR", 1, 1, 0]], "telemetry": {"sent": 0, "dropped": 0, "errors": 1, "invalid": 0, "attempts": 2, "spins": 1, "yields": 0, "final_level": 0, "final_credits": 999999999999999999999999999999}}
candidate {"packets": [["ERROR", 1, 1, 0]], "telemetry": {"sent": 0, "dropped": 0, "errors": 1, "invalid": 0, "attempts": 2, "spins": 1, "yields": 0, "final_level": 1, "final_credits": 999999999999999999999999999999}}
```

The submitted reading, `adversarial`, is in the largest cluster (6 of 7), but it was chosen for agreeing with the independent reference rather than for the size of its cluster. The divergence is reported rather than resolved: a unanimous cluster is not evidence that the clause was read correctly.

---

## `1c182498c9c7`, rust, `main`

*Simulate transmitting a UTF-8 text range through byte-limited chunks with segment boundaries and budget constraints.*

**Stated maximum:** N=500,000 characters; S up to 500,000 segments; Q=500,000 requests; C and H up to 10^18.

**6 traps quoted:**

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > A chunk cannot cross a source-segment boundary. Reaching that boundary closes it.

  *quoted from the statement*

  Missing it produces: Ignoring segment boundaries produces wrong chunk counts, wire_bytes, and last_chunk_payload.

  Required instead: Explicitly track segment end positions and close chunks when a segment ends, even if C is not reached.

- **INDEXING**: an index convention that differs from the usual one
  > one-based positions and... 1 <= L <= R <= N

  *quoted in pieces, across an elision*

  Missing it produces: Off-by-one errors when converting between 1-based problem indices and 0-based arrays.

  Required instead: Consistently convert: problem position P maps to array index P-1; output last as problem position, not array index.

- **MAGNITUDE**: a bound past the point where the obvious numeric type stops being safe
  > Rust wraps silently.

  *the model's wording, not the statement's*

  Missing it produces: Overflow during addition of wire_bytes contributions silently wraps to wrong values.

  Required instead: Use unsigned 64-bit types; carefully bound intermediate sums: (total + payload + H) must stay under 2×10^18.

- **DEGENERATE**: a degenerate input with a specified, non-obvious result
  > A header is never sent without at least one character. If this would exceed B, stop before that character.

  *quoted in pieces, across an elision*

  Missing it produces: If budget is insufficient for first character (payload + header), output is last=0, chunks=0, with cause=LIMIT.

  Required instead: Before sending any character, check if payload + (H if starting chunk) ≤ B; if not, return early with zeroed counts.

- **OUTPUT**: an output shape that is easy to get subtly wrong
  > Completing the requested range has cause `END`; every earlier stop has cause `LIMIT`.

  *quoted from the statement*

  Missing it produces: Misspelling 'END' or 'LIMIT' (e.g., 'FINISHED', 'DONE') fails exact output token comparison.

  Required instead: Output the exact strings 'END' or 'LIMIT' based on whether all characters in [L, R] were transmitted.

- **UNITS**: two different units of measurement used for the same thing
  > UTF-8, a value uses 1 byte for U+0000..U+007F, 2 for U+0080..U+07FF, 3 for U+0800..U+FFFF, and 4 otherwise.

  *quoted from the statement*

  Missing it produces: Confusing payload_bytes with character count: a 4-byte character adds 4 to payload_bytes, not 1.

  Required instead: Track payload_bytes as sum of per-character UTF-8 widths; track characters as count of characters sent.

**Verification:** 18 generated inputs, 2 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `=======!==========`: adversarial, plain, traps
- `==================`: edgefirst, restate
- `=======!====!!!!!!`: complexity

First divergence, framing `plain`, case `small#23061`:

```
input     14 1 12 9 0
C 2D 424 F57F 2C 52 469 7D9 5C 9AFB 182 F0 325 3B0
14
1 6 61
4 6 48
13 14 3
2 11 18
13 13 79
14 14 6
14 14 38
11 11 55
1 3 64
5 11 53
9 11 62
2 3 78
reference 9 9 6 6 1 9 END
5 5 3 6 1 5 END
2 2 1 13 1 2 LIMIT
18 18 10 11 3 2 END
2 2 1 13 1 2 END
2 2 1 14 1 2 END
2 2 1 14 1 2 END
2 2 1 11 1 2 END
4 4 3 3 1 4 END
12 12 7 11 2 5 END
6 6 3 11 1 6 END
3 3 2 3 1 3 END

candidate 9 9 6 6 1 9 END
5 5 3 6 1 5 END
2 2 1 13 1 2 LIMIT
18 18 10 11 6 18 END
2 2 1 13 1 2 END
2 2 1 14 1 2 END
2 2 1 14 1 2 END
2 2 1 11 1 2 END
4 4 3 3 1 4 END
12 12 7 11 3 12 END
6 6 3 11 1 6 END
3 3 2 3 1 3 END

```

**A minority reading was submitted.** `restate` sits in a cluster of 2 of 7, against a largest cluster of 3. It was submitted because it agreed with the independently generated reference and the larger cluster did not. This is the case a majority vote gets wrong by construction, and it is why the ranking has no term for cluster size.

---

## `1dea32802072`, python, `track_indicator`

*Tracks indicator index of a selected tab in an ordered strip through insert, remove, and reverse operations.*

**Stated maximum:** 300,000 total identifiers across initial_ids and all inserts; 200,000 operations; reverse ranges unbounded.

**6 traps quoted:**

- **REDEFINITION**: a standard term redefined to mean something else
  > An existing selection remains attached to the same identifier.

  *quoted from the statement*

  Missing it produces: Tracking selection as position causes wrong index after insert/remove/reverse change positions.

  Required instead: Track which identifier is selected, not its position; map to position when needed.

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > use the order immediately before this operation... select the first surviving tab to its right

  *quoted in pieces, across an elision*

  Missing it produces: Cannot determine which tabs are to the right without pre-removal positions and order.

  Required instead: Record pre-removal order and positions before any removals; find survivors by original index.

- **PRECEDENCE**: numbered rules that must be applied in order, first match winning
  > Remove them simultaneously.

  *quoted from the statement*

  Missing it produces: Wrong selection if selection rule applied after each removal instead of once at end.

  Required instead: Remove all identifiers atomically; apply selection rule once after all are removed.

- **DEGENERATE**: a degenerate input with a specified, non-obvious result
  > If the strip was empty, the first inserted identifier becomes selected.

  *quoted from the statement*

  Missing it produces: Empty strip after insert remains unselected instead of selecting the first inserted ID.

  Required instead: Check if strip was empty before insert; select first inserted ID if so.

- **OUTPUT**: an output shape that is easy to get subtly wrong
  > After every operation, append the current indicator index to the result

  *quoted from the statement*

  Missing it produces: Returning initial index as first element even with zero operations; wrong output shape.

  Required instead: Build result list only by appending after each operation; will be empty if none.

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > positions from `left` through `right - 1`

  *quoted from the statement*

  Missing it produces: Off-by-one reversal error leaves all positions wrong after reverse operation.

  Required instead: Reverse positions [left, right) with right as exclusive upper bound; use correct indexing.

**Verification:** 18 generated inputs, 0 of 7 candidates agreed with the independent reference on all of them.

---

## `2beff58fa923`, python, `refresh_references`

*Match references to entries across snapshot states, returning (status, namespace, location, hash).*

**Stated maximum:** 200,000 snapshots, entries, updates, references; 1,000,000 induced candidate names.

**6 traps quoted:**

- **REDEFINITION**: a standard term redefined to mean something else
  > a function match changes the namespace to "function"

  *quoted from the statement*

  Missing it produces: Value reference matching function incorrectly returns namespace='value'.

  Required instead: Update namespace to 'function' when value reference matches function candidate.

- **REDEFINITION**: a standard term redefined to mean something else
  > Once matched, the reference becomes location-authoritative immediately and for all later

  *quoted from the statement*

  Missing it produces: Matched reference re-matched at later snapshots; hash incorrectly updated.

  Required instead: Track matched references; skip re-matching once location-authoritative.

- **UNITS**: two different units of measurement used for the same thing
  > `N` is `0` or a positive decimal integer without leading zeroes

  *quoted from the statement*

  Missing it produces: Suffix @01 incorrectly parsed as valid; reference treated as valid.

  Required instead: Reject @N if N has leading zero unless N is exactly '0'.

- **REDEFINITION**: a standard term redefined to mean something else
  > prepending the longest through shortest prefix of `context` to qualified parsed name

  *quoted in pieces, across an elision*

  Missing it produces: Candidates checked in wrong order; reference matches wrong entry or misses.

  Required instead: Check candidates in exact longest-to-shortest order with first-match-wins.

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > `start` is an integer from 0 through `len(snapshots)`

  *quoted from the statement*

  Missing it produces: References with start=len(snapshots) skipped if only 0..len(snapshots)-1 assumed.

  Required instead: Snapshot states span 0 to len(snapshots) inclusive, not 0 to len-1.

- **COMPLEXITY**: a size at which the obvious approach is a wrong answer
  > at most 200,000 snapshots, entries, updates, and references each

  *quoted from the statement*

  Missing it produces: Naive O(n²) checking every reference at every snapshot times out.

  Required instead: Use dict/set lookups for O(1) candidate existence checks per snapshot.

**Verification:** 18 generated inputs, 3 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `==================`: adversarial, literal
- `============!!!!!!`: edgefirst, plain, traps
- `======!!!!!!!!!!!!`: restate
- `======XXXXXXXXXXXX`: complexity

First divergence, framing `traps`, case `medium#7713`:

```
input     [[{"namespace": "type", "name": "Typ0", "version": null, "hash": "ih0"}, {"namespace": "type", "name": "Typ1", "version": null, "hash": "ih1"}, {"namespace": "type", "name": "Typ2", "version": null, "hash": "ih2"}, {"namespace": "type", "name": "Typ3", "version": null, "hash": "ih3"}, {"namespace": "type", "name": "Typ4", "version": null, "hash": "ih4"}, {"namespace": "type", "name": "Typ5", "vers... (10298 chars)
reference [["located", "type", "l0", "rh0"], ["located", "type", "l1", "rh1"], ["located", "type", "Typ2", "ih2"], ["missing", "function", null, null], ["located", "function", "l4", "rh4"], ["located", "function", "l5", "rh5"], ["missing", "value", null, null], ["missing", "value", null, null], ["located", "value", "l8", "rh8"], ["located", "type", "l9", "rh9"], ["located", "type", "Typ10", "ih10"], ["locat... (1021 chars)
candidate [["located", "type", "l0", "ih0"], ["located", "type", "l1", "ih1"], ["located", "type", "Typ2", "ih2"], ["missing", "function", null, null], ["located", "function", "l4", "rh4"], ["located", "function", "l5", "rh5"], ["missing", "value", null, null], ["missing", "value", null, null], ["located", "value", "l8", "rh8"], ["located", "type", "l9", "ih9"], ["located", "type", "Typ10", "ih10"], ["locat... (1020 chars)
```

**A minority reading was submitted.** `adversarial` sits in a cluster of 2 of 7, against a largest cluster of 3. It was submitted because it agreed with the independently generated reference and the larger cluster did not. This is the case a majority vote gets wrong by construction, and it is why the ranking has no term for cluster size.

---

## `4e49a099fd84`, rust, `main`

*Partition UTF-8 string into graphemes by complex boundary rules; answer queries about grapheme sequences.*

**Stated maximum:** 600,000 UTF-8 bytes; 300,000 queries

**6 traps quoted:**

- **PRECEDENCE**: numbered rules that must be applied in order, first match winning
  > apply the first matching rule ... rule order is authoritative

  *quoted in pieces, across an elision*

  Missing it produces: Checking rules as accumulated conditions instead of first-match-wins produces wrong boundary positions.

  Required instead: Iterate rules 1, 6 in order; stop at first match and skip all remaining rules.

- **UNITS**: two different units of measurement used for the same thing
  > broadcasts use UTF-16 code-unit offsets ... larger scalar occupies two UTF-16 code units

  *the model's wording, not the statement's*

  Missing it produces: Outputting byte or grapheme offsets instead of UTF-16 code-unit positions produces wrong query answers.

  Required instead: Precompute UTF-16 offset for every grapheme boundary; output offsets/distances in UTF-16 code units.

- **COMPLEXITY**: a size at which the obvious approach is a wrong answer
  > Constraints: |S| <= 600,000 UTF-8 bytes and 1 <= Q <= 300,000

  *quoted from the statement*

  Missing it produces: O(|S|) per query = 1.8×10^11 operations; solution times out.

  Required instead: Precompute all boundaries and UTF-16 offsets in O(|S|); answer queries in O(1).

- **INDEXING**: an index convention that differs from the usual one
  > resolve index x to x when nonnegative and G+x when negative, then clamp to [0,G]

  *quoted in pieces, across an elision*

  Missing it produces: Clamping before resolving negative indices produces out-of-range or wrong indices.

  Required instead: Resolve negative indices first (x → G+x), then clamp result to [0,G].

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > If there are G graphemes, ... clamp it to [0,G]

  *quoted in pieces, across an elision*

  Missing it produces: Assuming G boundaries instead of G+1 causes off-by-one errors.

  Required instead: Recall G graphemes produce G+1 boundaries, indexed 0 through G inclusive.

- **REDEFINITION**: a standard term redefined to mean something else
  > Controls are U+0000..U+001F and U+007F..U+009F

  *quoted from the statement*

  Missing it produces: Checking only U+0000..U+001F and missing U+007F..U+009F causes wrong boundaries on extended ASCII controls.

  Required instead: Implement control check for both ranges: ASCII (U+0000, U+001F) AND extended (U+007F, U+009F).

**Verification:** 18 generated inputs, 7 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `=================`: adversarial, complexity, edgefirst, literal, restate, traps
- `=========X=X=XX==`: plain

The submitted reading, `edgefirst`, is in the largest cluster (6 of 7), but it was chosen for agreeing with the independent reference rather than for the size of its cluster. The divergence is reported rather than resolved: a unanimous cluster is not evidence that the clause was read correctly.

---

## `5cb294c18288`, python, `validate_build`

*Validate record-building operations on schemas with implicit flattened layouts and huge repetitions.*

**Stated maximum:** 200,000 schemas; 300,000 layout terms; 10^18 repetitions and capacities.

**6 traps quoted:**

- **MEMORY**: a structure that cannot be materialised at the stated maximum
  > Repetitions between 1 and 10^18. Flattened layouts may be enormous.

  *the model's wording, not the statement's*

  Missing it produces: Eagerly flattening all schemas causes memory exhaustion or timeout with 10^18 fields.

  Required instead: Represent flattened layouts implicitly; compute field positions without materializing full lists.

- **MAGNITUDE**: a bound past the point where the obvious numeric type stops being safe
  > default fills next k positions; k and repetitions reach 10^18.

  *the model's wording, not the statement's*

  Missing it produces: Iterating k times causes timeout; can't determine which fields k spans without iteration.

  Required instead: Use modular arithmetic over repeat lengths to determine fields spanned; avoid iterating k.

- **REDEFINITION**: a standard term redefined to mean something else
  > Descriptor equality is recursive and includes schema indices and capacities.

  *quoted from the statement*

  Missing it produces: Comparing only element type misses capacity mismatch; Array(int,100) wrongly equals Array(int,50).

  Required instead: Recursively check all parts: element type, schema indices, and array capacities.

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > Record closes only when all flattened fields filled. Array may close at any length.

  *the model's wording, not the statement's*

  Missing it produces: Enforcing full array fill or allowing partial record fill incorrectly rejects valid operations.

  Required instead: Verify all record fields filled before closing; allow arrays to close at any fill level.

- **INDEXING**: an index convention that differs from the usual one
  > Return 1-based index of earliest invalid operation.

  *the model's wording, not the statement's*

  Missing it produces: Off-by-one errors return 0-based index or len(operations) when 1-based or len(operations)+1 required.

  Required instead: Use 1-based indexing consistently for operation numbering in all return paths.

- **OUTPUT**: an output shape that is easy to get subtly wrong
  > Return 0 if valid and closed; len(operations)+1 if valid but open; else 1-based invalid index.

  *the model's wording, not the statement's*

  Missing it produces: Confusing the three cases returns wrong value: 0 when should be len+1, or invalid index when should be 0.

  Required instead: Clearly distinguish: return 1-based invalid index first, then 0 for closed, then len+1 for open.

**Verification:** 18 generated inputs, 3 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `=================`: adversarial, complexity, literal
- `!!=!=!=!!=!!!!!!!`: edgefirst, plain, restate, traps

First divergence, framing `edgefirst`, case `edge#28539`:

```
input     [[[["field", "arr", ["array", "int", 3]]]], 0, [["open", "arr", ["array", "int", 3]], ["default", 1], ["close"], ["close"]]]
reference 1
candidate 0
```

**A minority reading was submitted.** `complexity` sits in a cluster of 3 of 7, against a largest cluster of 4. It was submitted because it agreed with the independently generated reference and the larger cluster did not. This is the case a majority vote gets wrong by construction, and it is why the ranking has no term for cluster size.

---

## `5ce30ef9e5cf`, rust, `main`

*Manage reversible object attribute overlays with activations that can be started, stopped, and queried.*

**Stated maximum:** N,K,Q ≤ 200k; total replacements ≤ 200k; sum path lengths ≤ 400k

**6 traps quoted:**

- **PRECEDENCE**: numbered rules that must be applied in order, first match winning
  > resolve its path after all preceding replacements in that same activation have been applied

  *quoted from the statement*

  Missing it produces: Using stale values when paths depend on other replacements in activation

  Required instead: Resolve each path immediately before applying replacement, seeing current state

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > read and follow the object reference in every attribute except the last

  *quoted from the statement*

  Missing it produces: Following final attribute as reference instead of reading it as target cell

  Required instead: Follow L-1 attributes to reach target object, then read cell at attribute L

- **ORDERING**: an ordering requirement at a tie
  > restore that activation's remembered writes in reverse replacement order

  *quoted from the statement*

  Missing it produces: Restored values applied in wrong order, overwriting each other incorrectly

  Required instead: When restoring, iterate replacements in reverse order

- **ORDERING**: an ordering requirement at a tie
  > STOPALL stops all active activations from newest to oldest

  *quoted from the statement*

  Missing it produces: Restored values overwritten by subsequent restorations in wrong order

  Required instead: Stop activations in reverse order (newest/most-recent first)

- **OUTPUT**: an output shape that is easy to get subtly wrong
  > number of active activations followed by their IDs from oldest to newest on one line

  *quoted from the statement*

  Missing it produces: Wrong output format or ID order, failing test cases

  Required instead: Print count and IDs on same line, IDs in activation order (oldest first)

- **INDEXING**: an index convention that differs from the usual one
  > Remembered paths are never resolved again

  *quoted from the statement*

  Missing it produces: Re-resolving paths gets different cells after other activations change values

  Required instead: Store resolved cell reference when remembering, restore to that cell

**Verification:** 18 generated inputs, 7 of 7 candidates agreed with the independent reference on all of them.

---

## `5d02bd0e16ab`, rust, `main`

*Simulator for a demand-aware queue with multiple producer versions and branching ancestry.*

**Stated maximum:** N=150000, Q=150000, each operation O(N) state; demand up to 10^18.

**6 traps quoted:**

- **MEMORY**: a structure that cannot be materialised at the stated maximum
  > Operation `i` creates version `i` from earlier version `b`; versions may branch. N,Q <= 150000

  *the model's wording, not the statement's*

  Missing it produces: Materializing complete O(N)-sized snapshots for all Q versions requires O(Q×N) memory, exceeding limits.

  Required instead: Reconstruct version state from operation ancestry on demand; do not store full snapshots.

- **MAGNITUDE**: a bound past the point where the obvious numeric type stops being safe
  > `r` is unique integer in `0..1000000006` congruent to signed value modulo 1000000007.

  *the model's wording, not the statement's*

  Missing it produces: Using x % MOD directly for negative x produces negative r, yielding wrong hash values.

  Required instead: Use formula ((x % MOD) + MOD) % MOD to ensure r stays in [0, MOD).

- **INDEXING**: an index convention that differs from the usual one
  > N one-shot producers and queue tickets `0..N-1`. ... Producer IDs are `1..N`.

  *quoted in pieces, across an elision*

  Missing it produces: Confusing 1-indexed producer IDs with 0-indexed tickets causes off-by-one errors in slot access.

  Required instead: Keep producer IDs 1-indexed; queue and tickets 0-indexed; translate carefully at each use.

- **PRECEDENCE**: numbered rules that must be applied in order, first match winning
  > Unpublished slot stops draining. Value consumed only if `d>0`; then `c` advances. If `d=0`, stops before.

  *the model's wording, not the statement's*

  Missing it produces: Checking demand before unpublished, or merging rules, consumes values that should block draining.

  Required instead: Check unpublished first (immediate stop); only for values, test d>0; stop before consuming if d=0.

- **PRECEDENCE**: numbered rules that must be applied in order, first match winning
  > COMPLETE if `p=c=N`; WAITING if `c=p<N`; BLOCKED if `c<p` unpublished; BACKPRESSURE if value d=0.

  *the model's wording, not the statement's*

  Missing it produces: Checking status conditions out of listed order or merging them outputs wrong status strings.

  Required instead: Determine status by checking conditions in order; halt at first match (COMPLETE → WAITING → BLOCKED → BACKPRESSURE).

- **OUTPUT**: an output shape that is easy to get subtly wrong
  > For every `P`, print: `DRAIN m h status p c d` using the resulting state.

  *quoted from the statement*

  Missing it produces: Wrong token order, leading zeros in numbers, or omitted fields causes all outputs to fail token comparison.

  Required instead: Print one space-separated line per drain: DRAIN m h status p c d with numbers unpadded in decimal.

**Verification:** 18 generated inputs, 5 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `==================`: adversarial, edgefirst, literal, traps
- `!!!!!===!!!=!!!!!!`: restate
- `========!!==!!!!!!`: complexity
- `======XXXXXXXXXXXX`: plain

First divergence, framing `complexity`, case `small#2991`:

```
input     5 18
R 0 5
R 1 1
R 2 4
W 3 1 E
P 4
D 5 525
P 6
D 7 830
W 8 4 V 21588
P 9
W 10 5 V -18577
D 11 544
P 12
P 13
P 14
P 15
R 16 3
W 17 3 E
reference DRAIN 0 0 BLOCKED 3 0 0
DRAIN 0 0 BLOCKED 3 0 525
DRAIN 0 0 BLOCKED 3 0 1355
DRAIN 2 250725734 WAITING 3 3 1897
DRAIN 0 0 WAITING 3 3 1897
DRAIN 0 0 WAITING 3 3 1897
DRAIN 0 0 WAITING 3 3 1897

candidate DRAIN 0 0 BLOCKED 3 0 0
DRAIN 0 0 BLOCKED 3 0 525
DRAIN 0 0 BLOCKED 3 0 1355
DRAIN 2 250725734 WAITING 3 3 1897
DRAIN 2 250725734 WAITING 3 3 1897
DRAIN 2 250725734 WAITING 3 3 1897
DRAIN 2 250725734 WAITING 3 3 1897

```

The submitted reading, `traps`, is in the largest cluster (4 of 7), but it was chosen for agreeing with the independent reference rather than for the size of its cluster. The divergence is reported rather than resolved: a unanimous cluster is not evidence that the clause was read correctly.

---

## `6e43a08ec05a`, python, `normalize_protection`

*Transform protected cell ranges after row and column insertions and deletions*

**Stated maximum:** 30k rectangles, 30k edits, dimensions 10^9, output ≤200k intervals

**6 traps quoted:**

- **INDEXING**: an index convention that differs from the usual one
  > 1 <= index <= the relevant dimension

  *quoted from the statement*

  Missing it produces: Off-by-one errors in every row/column coordinate transformation

  Required instead: Recognize 1-based edit indices explicitly; convert carefully if using 0-based internally

- **COMPLEXITY**: a size at which the obvious approach is a wrong answer
  > Do not enumerate individual worksheet cells or rows

  *quoted from the statement*

  Missing it produces: O(max_row × max_col) solution times out despite correct algorithm on large inputs

  Required instead: Use coordinate compression or interval tracking; never iterate over rows or materialize grid

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > Delete lines index through index+d-1. Cells in them disappear, later cells move by -d, and the final d lines become unprotected

  *quoted from the statement*

  Missing it produces: Rectangles overlapping deletion range not split; coordinates not adjusted; final rows incorrectly tracked

  Required instead: Split rectangles that span deleted range; shift later coordinates by -d; treat final d rows as unprotected

- **ORDERING**: an ordering requirement at a tie
  > every maximal consecutive sequence of rows on which that exact maximal interval occurs becomes (first_row, c1, last_row, c2). Rectangles cannot be combined in any other way

  *quoted from the statement*

  Missing it produces: Rows merged across gaps or intervals merged incorrectly; output non-canonical

  Required instead: Merge only consecutive rows with identical maximal column interval; disallow any other combination

- **RANGES**: an inclusive or exclusive boundary that is easy to read the wrong way
  > cells moved beyond the fixed worksheet boundary are discarded

  *quoted from the statement*

  Missing it produces: Rectangles extend beyond [1, max_row] × [1, max_col]; output contains invalid coordinates

  Required instead: Clip all rectangle coordinates to [1, max_row] and [1, max_col] after each edit; discard empty results

- **OUTPUT**: an output shape that is easy to get subtly wrong
  > Sort the result lexicographically. Return [] for an empty union

  *quoted from the statement*

  Missing it produces: Output in arbitrary order or undefined behavior on empty set

  Required instead: Sort (r1,c1,r2,c2) tuples using default lexicographic ordering; handle empty result as []

**Verification:** 18 generated inputs, 2 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `==================`: adversarial, literal
- `!!=!===!====!!!!!!`: edgefirst, traps
- `!!=!===!====!!!!=!`: plain, restate
- `============!=!!=!`: complexity

First divergence, framing `complexity`, case `medium#7713`:

```
input     [[[39, 19, 69, 48], [50, 27, 53, 40], [10, 55, 14, 55], [72, 15, 80, 33], [51, 37, 74, 53], [72, 28, 82, 41], [3, 11, 47, 24], [30, 10, 35, 20], [19, 34, 65, 49]], [["column", 39, 1], ["row", 57, 1], ["column", 3, -1], ["column", 44, -3], ["column", 44, -3], ["column", 2, -2], ["row", 8, -2], ["row", 2, 2], ["column", 18, 1], ["row", 23, 1], ["column", 35, 1], ["row", 48, 3], ["column", 36, -3], [... (480 chars)
reference [[5, 8, 9, 17], [5, 19, 9, 21], [10, 8, 14, 17], [10, 19, 14, 21], [10, 44, 14, 44], [15, 8, 18, 17], [15, 19, 18, 21], [19, 8, 22, 17], [19, 19, 22, 21], [19, 31, 22, 33], [19, 35, 22, 39], [24, 8, 30, 17], [24, 19, 30, 21], [24, 31, 30, 33], [24, 35, 30, 39], [31, 7, 36, 17], [31, 19, 36, 21], [31, 31, 36, 33], [31, 35, 36, 39], [37, 8, 39, 17], [37, 19, 39, 21], [37, 31, 39, 33], [37, 35, 39, 3... (797 chars)
candidate [[5, 8, 9, 17], [5, 19, 9, 21], [10, 8, 14, 17], [10, 19, 14, 21], [10, 44, 14, 44], [15, 8, 18, 17], [15, 19, 18, 21], [19, 8, 22, 17], [19, 19, 22, 21], [19, 31, 22, 33], [19, 35, 22, 39], [24, 8, 30, 17], [24, 19, 30, 21], [24, 31, 30, 33], [24, 35, 30, 39], [31, 7, 36, 17], [31, 19, 36, 21], [31, 31, 36, 33], [31, 35, 36, 39], [37, 8, 39, 17], [37, 19, 39, 21], [37, 31, 39, 33], [37, 35, 39, 3... (797 chars)
```

The submitted reading, `adversarial`, is in the largest cluster (2 of 7), but it was chosen for agreeing with the independent reference rather than for the size of its cluster. The divergence is reported rather than resolved: a unanimous cluster is not evidence that the clause was read correctly.

---

## `6eca8a9120e0`, python, `capture_binders`

*Identify declarations whose names appear free in replacements and occur on paths through those declarations in the expression DAG.*

**Stated maximum:** 250,000 total nodes across both structures; 500,000 child references plus declaration edges; linear graph depth.

**6 traps quoted:**

- **COMPLEXITY**: a size at which the obvious approach is a wrong answer
  > Graph paths and replacement-tree depth may be linear in the node count.

  *quoted from the statement*

  Missing it produces: O(n²) naive algorithms timeout; 250k × path-length iterations exceeds time limits.

  Required instead: Design solution respecting DAG structure; avoid per-node iteration over all paths.

- **REDEFINITION**: a standard term redefined to mean something else
  > a node may have multiple incoming child references. Its meaning for this task is its complete unfolding into a tree.

  *quoted in pieces, across an elision*

  Missing it produces: Incorrect capture detection; same var node represents multiple distinct occurrences with different scopes.

  Required instead: Process all paths to each node or conceptually unfold DAG; do not process each node occurrence once.

- **REDEFINITION**: a standard term redefined to mean something else
  > An original declaration is capturing if there exists at least one replaced occurrence such that: the occurrence's path crosses the scoped edge introducing that declaration, and the declaration's name is free in the replacement.

  *quoted in pieces, across an elision*

  Missing it produces: Misidentified capturing declarations; only path crossing OR only free-in-replacement is insufficient.

  Required instead: Check both conditions for every replaced occurrence: scoped edge crossed AND name is free in replacement.

- **REDEFINITION**: a standard term redefined to mean something else
  > A bind, let, or match term type defines distinct scope rules for declarations, body, and auxiliary terms.

  *the model's wording, not the statement's*

  Missing it produces: Wrong scope analysis; declarations applied over wrong subterms; incorrect capture detection.

  Required instead: Implement exact per-term-type scope rules; track which subterms fall under which declarations.

- **REDEFINITION**: a standard term redefined to mean something else
  > Every auxiliary term uses the scope surrounding the whole `match`, not the arm's scope.

  *quoted in pieces, across an elision*

  Missing it produces: Auxiliary terms incorrectly analyzed as if in arm scope; wrong declarations active.

  Required instead: Evaluate auxiliaries in outer match scope; do not include arm-local declarations in auxiliary scope.

- **REDEFINITION**: a standard term redefined to mean something else
  > the declaration's name is free in the replacement

  *quoted from the statement*

  Missing it produces: False negatives or false positives; missing capture or over-reporting if free-variable analysis is incomplete.

  Required instead: Traverse entire replacement tree; identify all names bound by replacement's declarations and subtract from all names.

**Verification:** 18 generated inputs, 5 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `==================`: adversarial, edgefirst, literal, plain, restate
- `=====!=!!!!=======`: traps
- `XXXXXXXXXXXXXXXXXX`: complexity

First divergence, framing `traps`, case `edge#39924`:

```
input     [[["var", "x"], ["var", "x"], ["bind", [[1, "x"]], 1]], 2, "x", 0]
reference []
candidate [1]
```

The submitted reading, `edgefirst`, is in the largest cluster (5 of 7), but it was chosen for agreeing with the independent reference rather than for the size of its cluster. The divergence is reported rather than resolved: a unanimous cluster is not evidence that the clause was read correctly.

---
