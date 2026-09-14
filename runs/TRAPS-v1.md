# Traps, per problem

Across 10 statements the trap pass quoted **54 clauses** that change the answer if read the usual way instead of the way they are written. On **5** of them, candidates written from different readings then behaved differently on the same input — a disagreement about meaning, not about typing.

Every quote below was copied from the statement by the trap pass during a recorded run, and every disagreement shows the input that produced it. Regenerate with `python traps_report.py runs/bench -o TRAPS.md`.

## Why this file exists

Sampling one prompt N times varies the seed. It does not vary the reading, so a misread clause is misread by all N candidates at once and the majority is unanimously wrong. Behavioural clustering removes generation noise and leaves statement misinterpretation untouched — that is the measured residual in [2506.11021](https://arxiv.org/abs/2506.11021), and it is this benchmark's whole difficulty. So the seven candidates are written from seven different reading strategies, and where they split, the split is recorded here rather than voted away.

---

## `1ba0d34fae43` — python, `simulate_writes`

*Simulate a congestion-aware write worker with per-packet retry scheduling, credit deduction, and implicit error handling.*

**Stated maximum:** 200,000 packets; 200,000 outcome runs with cumulative count up to 10^18 events

**6 traps quoted:**

- **PRECEDENCE** — numbered rules that must be applied in order, first match winning
  > Another attempt scheduled only if... credit balance at least cost. Scheduling deducts exactly cost credits.

  Missing it produces: Deducting on every 'full' without checking conditions causes negative balances or incorrect drops.

  Required instead: Check both retries_scheduled < max_retries AND credit_balance >= cost before deducting; drop if either fails.

- **COMPLEXITY** — a size at which the obvious approach is a wrong answer
  > run-length encoded chronological list; run counts at most 10**18

  Missing it produces: Expanding outcome events into individual entries causes memory exhaustion and timeout.

  Required instead: Process outcomes as runs; track current run index and position within run without expanding.

- **DEGENERATE** — a degenerate input with a specified, non-obvious result
  > After all runs exhausted, every later attempt implicitly returns error

  Missing it produces: Solutions assuming sufficient outcomes crash when outcome list is fully consumed.

  Required instead: Track outcome exhaustion; provide implicit 'error' outcomes thereafter (reset level, no credit change).

- **PRECEDENCE** — numbered rules that must be applied in order, first match winning
  > performs exactly one scheduler yield if 2**old_level > spin_limit

  Missing it produces: Using cost > spin_limit for yield condition produces wrong yield counts.

  Required instead: Yield based on 2**old_level > spin_limit, not on whether cost is capped.

- **REDEFINITION** — a standard term redefined to mean something else
  > packet valid exactly when length in [1, 65535]. Invalid packets make no attempt.

  Missing it produces: Assuming all packets valid produces wrong statuses and missing invalid packet count.

  Required instead: Validate length before processing; if invalid, mark INVALID and skip outcome consumption entirely.

- **OUTPUT** — an output shape that is easy to get subtly wrong
  > one (status, retries, spins, yields) tuple per input length

  Missing it produces: Outputting results in attempt processing order breaks correspondence between packets and tuples.

  Required instead: Track original packet index; output tuples in input packet order, not processing order.

**Verification:** 18 generated inputs, 7 of 7 candidates agreed with the independent reference on all of them.

---

## `1c182498c9c7` — rust, `main`

*Transmit Unicode text in byte-limited chunks with headers, respecting segment boundaries and budget constraints.*

**Stated maximum:** N=500k, Q=500k, C=10^18, H=10^18, B=10^18

**6 traps quoted:**

- **MAGNITUDE** — a bound past the point where the obvious numeric type stops being safe
  > The request budget B limits total wire bytes: payload bytes plus headers.

  Missing it produces: Computing chunks * H overflows i64 when both values are near 10^18 bounds.

  Required instead: Recognize worst case: N segments, each its own chunk; use u64 or overflow-safe arithmetic for wire_bytes.

- **RANGES** — an inclusive or exclusive boundary that is easy to read the wrong way
  > A chunk cannot cross a source-segment boundary. Reaching that boundary closes it.

  Missing it produces: Chunks span segments if boundaries are not forced to close; wrong character and chunk counts.

  Required instead: Compute segment boundaries as cumulative character positions; force chunk closure when last char of segment is reached.

- **UNITS** — two different units of measurement used for the same thing
  > Next S positive integers: source-segment lengths whose sum is N.

  Missing it produces: Treating segment lengths as byte counts instead of character counts shifts all boundary positions.

  Required instead: Segment lengths are character counts matching N; accumulate as character positions, not bytes.

- **DEGENERATE** — a degenerate input with a specified, non-obvious result
  > If this would exceed B, stop before that character. A header is never sent without at least one character.

  Missing it produces: Outputting non-zero chunks, payload, or wire_bytes when first character + header exceeds B.

  Required instead: Check if width(L) + H > B before any transmission; if true, set last=0, chunks=0, cause=LIMIT immediately.

- **PRECEDENCE** — numbered rules that must be applied in order, first match winning
  > Before sending a character, include its payload width and, if it would begin a new chunk, one header. If this would exceed B, stop before that character.

  Missing it produces: Off-by-one: transmitting one character too many or too few if budget check uses >= instead of >.

  Required instead: Check current_wire + char_width + (H if new_chunk) > B strictly; stop if true without sending character.

- **INDEXING** — an index convention that differs from the usual one
  > with one-based positions and 1 <= L <= R <= N

  Missing it produces: Off-by-one errors in converting one-based L, R to zero-based array indices; wrong character range processed.

  Required instead: Consistently convert L, R to zero-based by subtracting 1; document and verify at every access point.

**Verification:** 10 generated inputs, 6 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `==!=======` — adversarial
- `==========` — complexity, edgefirst, literal, plain, restate, traps

First divergence, framing `adversarial`, case `edge#64795`:

```
input     1 1 3 10 0
41
1
1 1 100
1 1 0
1 1 1
reference 1 1 1 1 1 1 END
0 0 0 0 0 0 LIMIT
1 1 1 1 1 1 END

candidate 1 1 1 1 1 1 END
0 0 0 0 0 0 END
1 1 1 1 1 1 END

```

The majority reading was submitted, and this divergence is reported rather than hidden: a unanimous cluster is not evidence that the clause was read correctly.

---

## `1dea32802072` — python, `track_indicator`

*Tracks the index of the selected tab after insert, remove, and reverse operations on a tab strip.*

**Stated maximum:** 300,000 total identifiers, 200,000 operations, unbounded reverse range lengths

**6 traps quoted:**

- **RANGES** — an inclusive or exclusive boundary that is easy to read the wrong way
  > reverse the order of all tabs at positions from left through right - 1

  Missing it produces: Off-by-one error: reversing [left, right] inclusive instead of [left, right) exclusive

  Required instead: Implement half-open interval as list[left:right], not list[left:right+1]

- **ORDERING** — an ordering requirement at a tie
  > select the first surviving tab to its right; if none exists, select the last surviving tab to its left

  Missing it produces: Selects wrong tab if left-first precedence applied or order reversed

  Required instead: Search right strictly before left; apply conditions in exact stated order, first-match-wins

- **REDEFINITION** — a standard term redefined to mean something else
  > Selection remains attached to the same identifier.

  Missing it produces: Position-based tracking breaks: selected index shifts when tabs inserted/removed before it

  Required instead: Track selected by identifier ID, not position; recompute position from current order each operation

- **PRECEDENCE** — numbered rules that must be applied in order, first match winning
  > use the order immediately before this operation and disregard every removed tab other than the selected tab

  Missing it produces: Using post-removal positions for right/left search yields wrong surviving tab

  Required instead: Cache pre-removal order before applying removes; search direction from pre-removal position

- **DEGENERATE** — a degenerate input with a specified, non-obvious result
  > if none survives, leave the strip unselected. If the strip was empty, the first inserted becomes selected.

  Missing it produces: Crash or logic error if code assumes selection always exists; -1 to id transition broken

  Required instead: Handle selected_id == -1 state throughout; insert correctly transitions empty strip to selected

- **COMPLEXITY** — a size at which the obvious approach is a wrong answer
  > Reversed ranges have no bound on their combined length.

  Missing it produces: Naive reversal per operation could TLE: 200k ops × 300k items quadratic cost

  Required instead: Ensure each operation is O(n) amortized; avoid rebuilding entire list per reverse

**Verification:** 18 generated inputs, 5 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `==================` — adversarial, edgefirst, literal, plain, restate
- `======!=!===!=!==!` — traps
- `!!!!!!!!!!!!!!!!!!` — complexity

First divergence, framing `traps`, case `small#6344`:

```
input     [[100000], 0, [["remove", [100000]], ["insert", 0, [100001, 100003, 100002]], ["insert", 2, [100003]], ["reverse", 1, 3], ["remove", [100002, 100001]], ["insert", 0, [100004, 100005]], ["insert", 0, [100006, 100007]], ["remove", [100004, 100007]], ["insert", 2, [100008]]]]
reference [-1, 0, 0, 0, 0, 2, 4, 2, 3]
candidate [-1, 0, 0, 0, 1, 3, 5, 3, 4]
```

The majority reading was submitted, and this divergence is reported rather than hidden: a unanimous cluster is not evidence that the clause was read correctly.

---

## `2beff58fa923` — python, `refresh_references`

*Resolve references across versioned snapshots, tracking which namespace/location/hash they match.*

**Stated maximum:** 200k snapshots, 200k entries, 200k updates, 200k references; 1M induced candidate names total.

**6 traps quoted:**

- **INDEXING** — an index convention that differs from the usual one
  > The initial index is snapshot 0. Applying atomic batch i produces snapshot i.

  Missing it produces: Off-by-one errors: solution processes wrong snapshots or crashes on edge case start=len(snapshots).

  Required instead: Map batch index to snapshot: snapshots[k] produces snapshot k+1. Snapshot count = len(snapshots)+1.

- **ORDERING** — an ordering requirement at a tie
  > form candidates by prepending the longest through shortest prefix of context

  Missing it produces: Solution checks shortest prefix first; selects wrong candidate (ambiguity in direction).

  Required instead: Generate candidates with prefix length n, n-1, ..., 1, 0. Check in this order; select first match.

- **REDEFINITION** — a standard term redefined to mean something else
  > a function match changes the namespace to "function"

  Missing it produces: Solution returns input namespace even after matching function; output namespace wrong.

  Required instead: Track namespace changes: for value refs finding function match, return ("located", "function", ...).

- **OUTPUT** — an output shape that is easy to get subtly wrong
  > At each such snapshot, if its exact key exists, its hash becomes the entry's current hash

  Missing it produces: Solution returns original reference hash for located status; doesn't track snapshot-level updates.

  Required instead: For location-authoritative refs, re-check entry at each snapshot and update hash if key exists.

- **RANGES** — an inclusive or exclusive boundary that is easy to read the wrong way
  > start is an integer from 0 through len(snapshots)

  Missing it produces: Solution crashes or skips reference with start=len(snapshots), only checking final snapshot.

  Required instead: Handle start values 0 to len(snapshots) inclusive; process from snapshot start until end.

- **DEGENERATE** — a degenerate input with a specified, non-obvious result
  > text consists of zero or more module identifiers followed by a terminal. Any violation makes invalid.

  Missing it produces: Solution accepts malformed text (e.g., leading uppercase, @@ suffix) or rejects valid edge cases.

  Required instead: Validate: identifiers [a-zA-Z0-9_]+, modules start [a-z], types start [A-Z], suffix @N only on function/value.

**Verification:** 18 generated inputs, 0 of 7 candidates agreed with the independent reference on all of them.

---

## `4e49a099fd84` — rust, `main`

*Partition a UTF-8 string into custom-graphemes via 6 boundary rules, output grapheme indices as UTF-16 offsets, and find longest common suffix match.*

**Stated maximum:** 600,000 UTF-8 bytes, 300,000 queries, grapheme count up to ~600,000.

**6 traps quoted:**

- **UNITS** — two different units of measurement used for the same thing
  > output the UTF-16 offsets of boundaries i,j... A scalar at most U+FFFF occupies one UTF-16 code unit; a larger scalar occupies two.

  Missing it produces: Outputs byte offsets or UTF-8 positions instead of UTF-16 code-unit offsets, causing wrong answers for strings with emoji.

  Required instead: Track each grapheme boundary's UTF-8 byte position; decode scalars to count 1 or 2 UTF-16 units per scalar.

- **PRECEDENCE** — numbered rules that must be applied in order, first match winning
  > For each internal gap between adjacent Unicode scalar values, apply the first matching rule... rule order is authoritative.

  Missing it produces: Merges rule conditions or checks all rules instead of stopping at first match, causing false boundaries or missing boundaries.

  Required instead: Implement if-else-if chain: check rules 1, 2, 3, 4, 5 in order; stop on first true condition; use rule 6 as catch-all.

- **REDEFINITION** — a standard term redefined to mean something else
  > If the left scalar is U+200D, the right scalar is an Emoji, and the nearest scalar before that U+200D after skipping Attachments is an Emoji, there is no boundary.

  Missing it produces: Fails to skip Attachments when looking backward from U+200D, or misidentifies Emoji ranges, causing wrong boundaries.

  Required instead: When left is U+200D and right is Emoji: walk backward from U+200D skipping Attachment ranges, check final scalar is Emoji.

- **REDEFINITION** — a standard term redefined to mean something else
  > If both scalars are Regional Indicators, count the consecutive Regional Indicators ending at the left scalar. There is no boundary exactly when that count is odd.

  Missing it produces: Miscounts consecutive RI by starting from wrong position or not including left scalar, giving wrong parity check.

  Required instead: Count RI by walking backward from left scalar (inclusive) until hitting non-RI; apply no-boundary iff count is odd.

- **INDEXING** — an index convention that differs from the usual one
  > resolve an index x to x when nonnegative and G+x when negative, then clamp it to [0,G]

  Missing it produces: Clamps before resolving, or clamps to [1,G], causing invalid grapheme indices and wrong query results.

  Required instead: First compute resolved = (x if x >= 0 else G+x); then clamp(resolved, 0, G); apply this to both query indices.

- **COMPLEXITY** — a size at which the obvious approach is a wrong answer
  > for every 0<=k<L, grapheme i+k and grapheme j+k have identical UTF-8 byte sequences... 600,000 bytes and 300,000 queries

  Missing it produces: Naive byte-by-byte comparison per query gives O(Q*L*bytes) ≈ O(10^11), timing out.

  Required instead: Precompute grapheme boundaries and byte ranges; for each query, iterate in O(L) comparing byte ranges; handle early exit.

**Verification:** 18 generated inputs, 7 of 7 candidates agreed with the independent reference on all of them.

---

## `5cb294c18288` — python, `validate_build`

*Validates build operations on schema-backed records and arrays with flattened layouts*

**Stated maximum:** 200k schemas, 200k operations, 60 nesting depth, 10^18 repetitions and capacities

**6 traps quoted:**

- **COMPLEXITY** — a size at which the obvious approach is a wrong answer
  > Schema-reference and descriptor nesting are at most 60. Repetitions between 1 and 10^18

  Missing it produces: Naive recursive schema flattening causes exponential expansion; OOMs on moderately complex inputs

  Required instead: Compute flattened field counts and positions algebraically without materializing full layouts

- **INDEXING** — an index convention that differs from the usual one
  > Return the 1-based index of the earliest invalid operation

  Missing it produces: Uses 0-based indexing internally throughout; returns operation index off by one

  Required instead: Track operation numbers as 1-based from start or add 1 at return; preserve 0 and len(operations)+1 exactly

- **MAGNITUDE** — a bound past the point where the obvious numeric type stops being safe
  > Repetitions, capacities, and default counts are between 1 and 10^18

  Missing it produces: Attempts to iterate through or allocate for 10^18 elements; catastrophic time and memory blowup

  Required instead: Track counts and positions algebraically; skip large ranges without iteration or allocation

- **REDEFINITION** — a standard term redefined to mean something else
  > Descriptor equality is recursive and includes schema indices and capacities

  Missing it produces: Accepts partial descriptor matches; ignores schema index or capacity differences in nested descriptors

  Required instead: Recursively compare all descriptor components: element type, schema index, capacity, and further nesting

- **RANGES** — an inclusive or exclusive boundary that is easy to read the wrong way
  > An array may be closed at any length. A record may be closed only when all flattened fields are filled

  Missing it produces: Applies identical closure logic to both; rejects valid partial array closures or accepts incomplete record closures

  Required instead: Distinguish container type; arrays close unconditionally; records close only when all flattened fields filled

- **MEMORY** — a structure that cannot be materialised at the stated maximum
  > Flattened layouts may be enormous

  Missing it produces: Attempts to construct or store full flattened layout for large schemas; exceeds available memory

  Required instead: Represent state as stack of open containers with current position; compute field offsets on demand

**Verification:** 18 generated inputs, 3 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `==============!===` — adversarial, literal, plain
- `==================` — complexity, restate, traps
- `==============!=!=` — edgefirst

First divergence, framing `literal`, case `medium#7814`:

```
input     [[[["field", "items", ["array", "int", 3]], ["field", "name", "text"]]], 0, [["open", "items", ["array", "int", 3]], ["put", null, "int"], ["put", null, "int"], ["close"], ["put", "name", "text"], ["close"]]]
reference 0
candidate 2
```

The majority reading was submitted, and this divergence is reported rather than hidden: a unanimous cluster is not evidence that the clause was read correctly.

---

## `5ce30ef9e5cf` — rust, `main`

*Manages reversible overlays of object attribute replacements with independent activation scopes.*

**Stated maximum:** 200k objects, 200k cells, 200k commands; 200k total replacements; 400k total path length

**6 traps quoted:**

- **REDEFINITION** — a standard term redefined to mean something else
  > For each replacement, resolve its path after all preceding replacements in that same activation have been applied

  Missing it produces: Solution pre-resolves all paths, gets wrong cells on tests where path depends on prior replacements

  Required instead: Resolve each path after all prior replacements in its activation are applied to state

- **ORDERING** — an ordering requirement at a tie
  > STOPALL stops all active activations from newest to oldest. Each complete restoration occurs before the next

  Missing it produces: Solution stops oldest-to-newest instead, leaves cells with values from wrong activation order

  Required instead: Stop from newest to oldest by reversing active activation queue order when processing STOPALL

- **REDEFINITION** — a standard term redefined to mean something else
  > Each restoration writes the remembered value even if another activation later changed that cell

  Missing it produces: Solution writes current cell value instead of remembered value, loses earlier overlay changes

  Required instead: Use remembered values from before each replacement, not current cell state during restoration

- **ORDERING** — an ordering requirement at a tie
  > restore that activation's remembered writes in reverse replacement order

  Missing it produces: Solution restores replacements forward instead of reverse, cell ends in wrong intermediate state

  Required instead: Reverse the replacement list when restoring, process from last replacement to first

- **MEMORY** — a structure that cannot be materialised at the stated maximum
  > Attributes are in 1..=10^9

  Missing it produces: Solution indexes cells with array sized by attribute, crashes out-of-memory or panics

  Required instead: Use HashMap or BTreeMap keyed by (object, attribute) pair for sparse cell storage

- **REDEFINITION** — a standard term redefined to mean something else
  > The ID is guaranteed inactive before START, but may be reused after stopping

  Missing it produces: Solution stores state per ID globally, merges independent activations with same reused ID

  Required instead: Track each activation separately by ID, allow ID reuse only after previous activation stops

**Verification:** 18 generated inputs, 7 of 7 candidates agreed with the independent reference on all of them.

---

## `5d02bd0e16ab` — rust, `main`

*A multi-version queue simulator with demand-aware consumption, hash-tracked drains, and status reporting.*

**Stated maximum:** N=150000 producers, Q=150000 operations, demand per ancestry up to 10^18.

**6 traps quoted:**

- **MAGNITUDE** — a bound past the point where the obvious numeric type stops being safe
  > r is the unique integer in 0..1000000006 congruent to the signed value modulo 1000000007

  Missing it produces: Negative remainder in hash, wrong final hash output

  Required instead: Map signed i64 to [0, MOD) using ((x % MOD) + MOD) % MOD

- **RANGES** — an inclusive or exclusive boundary that is easy to read the wrong way
  > A value is consumed only if d>0; ... If d=0, draining stops before that value.

  Missing it produces: Consumes one extra value, wrong m count and hash h

  Required instead: Before consuming any value, check d>0; skip consuming if d=0 without advancing c

- **DEGENERATE** — a degenerate input with a specified, non-obvious result
  > An unpublished slot stops draining. A completion is consumed by advancing c. A value is consumed only if d>0.

  Missing it produces: Wrong events consumed, incorrect m, p, c, d in final state

  Required instead: For slot at c, check in order: if unpublished stop; if completion consume; if value check d

- **PRECEDENCE** — numbered rules that must be applied in order, first match winning
  > Operation i creates version i from earlier version b; versions may branch.

  Missing it produces: State mutations in base version leak to branches or vice versa, wrong output

  Required instead: Each version stores independent state for p, c, d, reservations, publications; branching copies, not shares

- **OUTPUT** — an output shape that is easy to get subtly wrong
  > Status is COMPLETE if p=c=N; WAITING if c=p<N; BLOCKED if c<p and slot c unpublished; BACKPRESSURE if c<p and slot c has value but d=0.

  Missing it produces: Wrong status output if conditions checked in wrong order or overlap

  Required instead: Ensure status logic checks all four conditions and returns exactly one; verify mutual exclusivity

- **INDEXING** — an index convention that differs from the usual one
  > Producer IDs are 1..N. Queue tickets 0..N-1. Producer s receives ticket p.

  Missing it produces: Off-by-one errors mapping producer ID to slot, wrong values consumed

  Required instead: Keep producer ID (1-indexed) separate from ticket index (0-indexed); map s to slot s-1 when accessing

**Verification:** 18 generated inputs, 5 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `XXXXXXXXXXXXXXXXXX` — adversarial, restate
- `==================` — edgefirst, literal, plain, traps
- `======XXXXXXXXXXXX` — complexity

The majority reading was submitted, and this divergence is reported rather than hidden: a unanimous cluster is not evidence that the clause was read correctly.

---

## `6e43a08ec05a` — python, `normalize_protection`

*Apply row/column edits to protected cell rectangles, output merged canonical rectangles*

**Stated maximum:** 30k rectangles, 30k edits, 10^9 dimensions, intermediate 150k rectangles, output ≤200k

**6 traps quoted:**

- **OUTPUT** — an output shape that is easy to get subtly wrong
  > every maximal consecutive sequence of rows on which that exact interval occurs becomes one

  Missing it produces: Output lists column-intervals per-row instead of merging rows with identical protected-column spans

  Required instead: After computing final protected cells per row, group and merge consecutive rows sharing column intervals

- **INDEXING** — an index convention that differs from the usual one
  > Edit index 1 <= index <= dimension, but rectangle coordinate indexing scheme: not stated

  Missing it produces: Off-by-one errors applying 1-indexed edits to 0-indexed rectangles or vice versa

  Required instead: Establish whether rectangles are 0-indexed or 1-indexed; apply all edits in consistent indexing space

- **RANGES** — an inclusive or exclusive boundary that is easy to read the wrong way
  > cells moved beyond the fixed worksheet boundary are discarded

  Missing it produces: Rectangles extending into rows/columns beyond max_row/max_col after insertion incorrectly survive

  Required instead: After each insertion, remove or clip rectangles with indices beyond max_row or max_col

- **MEMORY** — a structure that cannot be materialised at the stated maximum
  > Do not enumerate individual worksheet cells or rows. Dimensions at most 10^9

  Missing it produces: Out-of-memory or timeout attempting to materialize or loop through 10^9-row worksheet

  Required instead: Represent worksheet implicitly; track only rectangles as tuples, never iterate rows or create grid

- **RANGES** — an inclusive or exclusive boundary that is easy to read the wrong way
  > Delete lines index through index+d-1... final d lines become unprotected

  Missing it produces: Rectangles in deletion range clipped incorrectly, or final d lines incorrectly remain protected

  Required instead: Clip rectangles intersecting [index,index+d-1] completely; ensure rows (max_row-d+1..max_row) become unprotected

- **COMPLEXITY** — a size at which the obvious approach is a wrong answer
  > 30,000 edits, 150,000 rectangles, output 200,000 intervals. Do not enumerate

  Missing it produces: TLE from O(edits × rectangles) loop tracking each rectangle independently through all edits

  Required instead: Use efficient interval merging per edit (union, overlap detection); merge overlapping rectangles

**Verification:** 18 generated inputs, 0 of 7 candidates agreed with the independent reference on all of them.

**Readings disagreed.**

- `!=!!!==!!=!!!!!!!!` — adversarial
- `=======!!=!!!!!!!!` — literal
- `=======!==!=!!!!!!` — edgefirst, restate, traps
- `=======!==!!!!!!!!` — complexity
- `=======!==!=!!!!=!` — plain

First divergence, framing `plain`, case `small#32419`:

```
input     [[[32, 31, 48, 35], [16, 28, 41, 37], [17, 29, 34, 35], [31, 8, 35, 33], [26, 8, 61, 15]], [["column", 3, 3], ["row", 32, -2]], 61, 37]
reference [[16, 31, 25, 40], [26, 11, 30, 18], [26, 31, 30, 40], [31, 11, 33, 40], [34, 11, 39, 18], [34, 31, 39, 40], [40, 11, 46, 18], [40, 34, 46, 38], [47, 11, 59, 18]]
candidate [[16, 31, 25, 37], [26, 11, 30, 18], [26, 31, 30, 37], [31, 11, 33, 37], [34, 11, 39, 18], [34, 31, 39, 37], [40, 11, 46, 18], [40, 34, 46, 37], [47, 11, 59, 18]]
```

The majority reading was submitted, and this divergence is reported rather than hidden: a unanimous cluster is not evidence that the clause was read correctly.

---

## `6eca8a9120e0` — python, `capture_binders`

*(analysis returned no parsable JSON)*

The trap pass returned nothing for this statement. That is a gap in the run, not a statement without traps.

**Verification:** 18 generated inputs, 0 of 7 candidates agreed with the independent reference on all of them.

---
