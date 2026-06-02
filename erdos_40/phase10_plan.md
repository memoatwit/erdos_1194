# Phase 10 — Erdős Problem #40 ($B_3$ growth)

## Problem statement

> Let $A \subset \mathbb{N}$ be an infinite set such that the triple sums
> $a + b + c$ for $a, b, c \in A$ are all distinct, aside from the
> trivial coincidences. Is it true that
> \[
>    \liminf_{N \to \infty} \frac{|A \cap [1, N]|}{N^{1/3}} \;=\; 0?
> \]

A set satisfying this property is a $B_3$ set. The trivial coincidences
are reorderings: $a + b + c = b + a + c$ etc. So really the condition is
that the multiset $\{a, b, c\}$ is uniquely recoverable from $a + b + c$.

**Source.** [erdosproblems.com/40](https://www.erdosproblems.com/40),
\$500 prize. **Open.**

## State of the art

- **Finite $B_3$ max:** $f_3(N) := \max\{|A| : A \subset [1, N],\
  A\ \text{is } B_3\}$ satisfies $f_3(N) \sim N^{1/3}$. Bose-Chowla
  construction gives $\ge (1 + o(1)) N^{1/3}$; Green's upper bound
  gives $\le (7/2)^{1/3} N^{1/3} + o(N^{1/3}) \approx 1.519\, N^{1/3}$.
- **Infinite $B_3$ density i.o.:** Best i.o. lower bound is
  $\gg N^{\sqrt 2 - 1 + o(1)} \approx N^{0.414}$ (Ruzsa). Above
  $N^{1/3}$, so density i.o. is well above the question's scale.
- **The question** is therefore: must every infinite $B_3$ set $A$
  have density *dropping arbitrarily low* relative to $N^{1/3}$ at
  some scales? Or can a single infinite $B_3$ set sustain density
  $\geq c N^{1/3}$ for some $c > 0$ at *every* $N$?

## Relation to our existing toolkit

The $B_2 = $ Sidon analog of #40 is solved (Erdős, classical: liminf = 0
for Sidon). Our Phase 2C partition argument achieves the analogous
result for PDS ($B_2[1]$ sets — perfect difference sets). For general
$B_2 = $ Sidon, the result follows from Erdős's i.o. Sidon-density
theorem (Halberstam-Roth).

For $B_3$, the natural attack is:

1. **Adapt the Phase 2C partition identity** to triple-sum form.
   Phase 2C says: for any infinite PDS, $a_n \gg n^{2-o(1)}$ i.o., which
   translates to density i.o. dropping like $n^{1/(2c)}$ for any
   $c < 2$. The triple-sum analog should give density i.o. dropping
   like $n^{1/(3c)}$ or similar — possibly enough to bracket the
   $N^{1/3}$ question.

2. **Existing argument template.** Generic Erdős i.o. density arguments
   for $B_h$ sets use Cauchy-Schwarz on the representation function.
   Need to check what's in the literature (Halberstam-Roth Ch. III).

## Phase 10 session plan

### Session 1 (this one)

- Set up directory.
- Build $B_3$ verifier and finite max-$B_3$ computer ($f_3(N)$).
- Implement greedy Mian-Chowla-for-$B_3$.
- Tabulate $f_3(N)$ for small $N$ to compare against the known
  $\sim N^{1/3}$ scaling.
- Inspect greedy $B_3$ sequence density empirically.

### Session 2

- Adapt the Phase 2C partition argument to $B_3$ form.
- Identify the right "anchor" and "gap" structure.
- Derive an analog of "for $c < ?$, $a_n \leq C n^c$ for all $n$
  gives a contradiction".

### Session 3

- Empirically check whether the partition argument's natural
  contradiction exponent matches the $N^{1/3}$ question scale.
- If yes: try to make it rigorous, write up.
- If no: identify the structural gap.

## Files (to be created)

- `solve_40.py` — Python verifier and small-$N$ optimisation.
- `b3_greedy.py` — Greedy $B_3$ generator (Mian-Chowla analog).
- `phase10_summary.md` — Findings.

## Realistic expectation

#40 has been open since Erdős and has a \$500 prize. We are NOT
likely to solve it. The reasonable goals for this phase:

- **Empirical:** generate $B_3$ data, see structure.
- **Analytical:** see whether Phase 2C-style partition arguments
  adapt.
- **Honest:** if no fresh angle emerges in 2-3 sessions, document
  what we tried and stop.
