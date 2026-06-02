# Survey of open Erdős problems — Sidon / additive basis / additive combinatorics

Goal: identify an open problem where our toolkit (CP-SAT exact search at
small $N$, partition / convolution identities for unique-representation
problems, extension-cost diagnostics, seeded-greedy / block-structured
constructions) has the best chance of producing a *new theorem*.

## Candidates

Filtered by tag (Sidon sets, additive basis, additive combinatorics) and
"open" status as of 2026-05. Recently-solved problems are noted.

### #39 — infinite Sidon density

> Is there an infinite Sidon set $A \subset \mathbb{N}$ such that
> $|A \cap [1,N]| \gg_\varepsilon N^{1/2 - \varepsilon}$ for every $\varepsilon > 0$?

- Status: **open**.
- Bounty: \$25 (Erdős) for any $A \gg N^c$ with $c > 1/3$; \$100 for any
  $\omega(N) N^{1/3}$ with $\omega \to \infty$.
- Current state: best i.o. density $\gg N^{\sqrt 2 - 1 + o(1)}$ (Ruzsa).
- Toolkit fit: density bound; partition; same family as our Phase 2A.
- Tractability: low. Open since Erdős; would need a genuinely new
  construction or sharper density-counting bound.

### #40 — $B_3$ growth (\$500 prize)

> Let $A \subset \mathbb{N}$ have all triple sums $a+b+c$ distinct
> (a $B_3$ set, aside from trivial coincidences). Is
> $\liminf |A \cap [1, N]|/N^{1/3} = 0$?

- Status: **open**, \$500 prize.
- Current state: Greedy gives $\gg N^{1/3}$; AKS got $\gg (N \log N)^{1/3}$;
  Ruzsa $\gg N^{\sqrt 2 - 1 + o(1)}$.
- Toolkit fit: density / partition identity for $B_3$ analogue
  (uniqueness of $a+b+c$ rather than $a-b$). Our Phase 2C partition
  argument adapts to triple-sum form; we have NOT explored this.
- Tractability: high-EV but probably hard.

### #41 / #42 — Sidon disjoint-difference sets, existence

> For every Sidon $A \subset [1, N]$, does there exist Sidon
> $B \subset [1, N]$ of size $M$ with $(A - A) \cap (B - B) = \{0\}$?

- Status: **SOLVED** by GPT 5.5 Pro (Sandhu), with ongoing discussion
  and Lean/formal verification activity on erdosproblems.com as of
  2026-05-14.
  Off the list.

### #43 — Sidon disjoint-difference sets, size bound (\$100 prize)

> If $A, B \subset [1, N]$ are Sidon with $(A - A) \cap (B - B) = \{0\}$,
> is $\binom{|A|}{2} + \binom{|B|}{2} \leq \binom{f(N)}{2} + O(1)$,
> where $f(N) = \max |A|$ over Sidon $A \subset [1, N]$?

- Status: **DISPROVED** as of 2026-05-14. The first question follows
  negatively from the solution to #42: take $|A| = f(N)$ and use #42 to
  find accompanying Sidon sets $B$ with $|B| \to \infty$, making the
  additive $O(1)$ gap impossible. Barreto's Bose--Chowla construction
  also gives a negative answer to the equal-size strengthening.
- Local note: the directory `erdos_42/` actually contains a CP-SAT attack
  on this #43 binomial-gap problem. It is useful as a verification harness,
  but it is no longer a live route to a new solution.

### #44 — Sidon set extension to near-maximal

> Is every Sidon $A \subset [1, N]$ extendable to a Sidon set
> in $[1, M]$ with size $\geq (1-\varepsilon) M^{1/2}$ for some $M$?

- Status: **SOLVED (Lean-verified)** in the affirmative.
  Off the list.

### #156 — maximal Sidon set, size $O(N^{1/3})$

> Does there exist a *maximal* Sidon set $A \subset [1, N]$ of size
> $O(N^{1/3})$?

(*Maximal* = $A$ is Sidon and no element of $[1, N] \setminus A$ can
be added without breaking the Sidon property.)

- Status: **open**.
- Current state: greedy maximal has size $\gg N^{1/3}$; Ruzsa
  constructed maximal $\ll (N \log N)^{1/3}$. Closing the
  $(\log N)^{1/3}$ gap is the natural sub-question.
- Toolkit fit: **high**. Direct CP-SAT formulation:
  - Variables: $y_i \in \{0, 1\}$ for $i \in [1, N]$.
  - Sidon: $\sum_{j-i = d} z_{i,j} \leq 1$ for every $d$
    (we already implemented this in Phase 4).
  - Maximality: for every $i \notin A$, adding $i$ creates a duplicate
    difference — encoded by a "blocking" constraint.
  - Objective: minimise $|A|$.
- Tractability: **medium**. Closing the $(\log N)^{1/3}$ gap analytically
  is hard, but computational ground-truth at $N \leq 100$ is in reach
  and may suggest the right scaling.

### #329 — Sidon density limsup

> What is $\sup_A \limsup_N |A \cap [1,N]|/\sqrt N$ over infinite
> Sidon sets $A$? Lower bound $1/\sqrt 2$ (Krückeberg); upper bound
> $1$ (Erdős–Turán).

- Status: **open**, identical-flavor to Phase 2A on #1194.
- Tractability: same difficulty as Phase 2A.

### #707 — Sidon-inside-PDS

> Best constant $c$ such that every "large enough" $A$ of $n$ reals
> with the $|B-B| \geq 11$ property contains a Sidon set of size
> $\geq cn$.

- Status: **open**, but recent progress in
  [arXiv:2510.19804](https://arxiv.org/abs/2510.19804) (Oct 2025,
  Forbidden Sidon subsets of perfect difference sets, human-assisted).
- Toolkit fit: PDS infrastructure directly applies.

## Comparison table

| # | Bounty | State of art | Toolkit fit | Tractability |
|---|---|---|---|---|
| 39 | \$25 / \$100 | $N^{\sqrt 2 - 1 + o(1)}$ i.o. (Ruzsa) | medium | low (Erdős-era) |
| 40 | \$500 | $N^{\sqrt 2 - 1 + o(1)}$ i.o. (Ruzsa) | medium | low |
| 42 | \$100 | $N + O(N^{3/4})$ | **high (CP-SAT)** | **medium** |
| 156 | — | $\gg N^{1/3}$, $\ll (N \log N)^{1/3}$ (Ruzsa) | **high (CP-SAT + greedy)** | **medium** |
| 329 | — | identical to Phase 2A | medium | low |
| 707 | \$100 | recent progress (arXiv:2510.19804) | high (PDS toolkit) | medium |

## Recommendation

**Current recommendation: #156 (maximal Sidon sets).**

#156 has no bounty, but it is still open, has zero comments on
erdosproblems.com as of 2026-05-14, and has a concrete logarithmic gap:
known maximal Sidon sets of size $\ll (N\log N)^{1/3}$ versus the natural
target $O(N^{1/3})$.

## Proposed first session on #156

1. **Implement a verifier** for Sidon and inclusion-maximal Sidon sets in
   $[1,N]$.
2. **Implement CP-SAT or custom DFS** to compute
   \[
   m(N)=\min\{|A|: A\subset [1,N]\text{ is maximal Sidon}\}.
   \]
3. **Tabulate exact values** for modest $N$, starting with
   $N \in \{10,15,20,25,30,35,40,50\}$.
4. **Inspect witnesses** for structure: residues, gap patterns, blocking
   mechanisms, and whether exact optima extend coherently.

See `erdos_156/phase9_plan.md` for the handoff and detailed modeling plan.

## Status

This survey replaces the "Open territory" line in `NEXT_PLAN.md`.
Recommended next phase: **Phase 9 — attack #156**, starting with the
minimum maximal-Sidon exact search in `erdos_156/phase9_plan.md`.
