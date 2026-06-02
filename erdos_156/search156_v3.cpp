// Exact fixed-size search for Erdos Problem #156, v3.
//
// v3 keeps the set of currently addable points as an incremental bitmask.
// This makes coverage pruning cheap enough to use at every node.
//
// Build:
//   clang++ -O3 -std=c++17 erdos_156/search156_v3.cpp -o erdos_156/search156_v3
//
// Usage:
//   erdos_156/search156_v3 95 6 600

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using Mask = unsigned __int128;
using std::size_t;

struct Stats {
    unsigned long long nodes = 0;
    unsigned long long leaves = 0;
    unsigned long long sidon_prunes = 0;
    unsigned long long coverage_prunes = 0;
};

static int popcount128(Mask m) {
    uint64_t lo = static_cast<uint64_t>(m);
    uint64_t hi = static_cast<uint64_t>(m >> 64);
    return __builtin_popcountll(lo) + __builtin_popcountll(hi);
}

struct Search {
    int N;
    int K;
    double limit_s;
    std::chrono::steady_clock::time_point start_time;
    Stats stats;
    std::vector<int> A;
    std::vector<int> answer;
    std::vector<int> future_cap;
    bool timed_out = false;
    bool coverage_order = true;

    Search(int n, int k, double limit)
        : N(n), K(k), limit_s(limit), start_time(std::chrono::steady_clock::now()) {
        A.reserve(K);
        future_cap.assign(K + 1, 0);

        // Safe upper bound on how many currently addable points one future
        // insertion can clear when current size is j:
        //   1 for the new element itself,
        //   2*C(j,2) for old used differences anchored at the new element,
        //   2*j*(j+1) for newly created differences anchored at all elements,
        //   j for new midpoint blockers.
        // This intentionally overcounts and is used only for safe pruning.
        for (int j = K - 1; j >= 0; --j) {
            int gain = 3 * j * j + 2 * j + 1;
            future_cap[j] = future_cap[j + 1] + gain;
        }
    }

    bool time_exceeded() {
        if (limit_s <= 0) return false;
        auto now = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double>(now - start_time).count();
        return elapsed > limit_s;
    }

    Mask initial_unblocked() const {
        Mask m = 0;
        for (int x = 1; x <= N; ++x) {
            m |= Mask(1) << x;
        }
        return m;
    }

    static void clear_point(Mask& m, int x, int N) {
        if (1 <= x && x <= N) {
            m &= ~(Mask(1) << x);
        }
    }

    Mask update_unblocked(int x, Mask diff_mask, Mask new_bits, Mask unblocked) {
        Mask out = unblocked;

        // The new element itself is no longer addable.
        clear_point(out, x, N);

        Mask new_diff_mask = diff_mask | new_bits;

        // Existing used differences, old and new, now block points around
        // the new anchor x. This is the part that a purely "new differences"
        // update misses.
        for (int d = 1; d <= N; ++d) {
            if ((new_diff_mask >> d) & Mask(1)) {
                clear_point(out, x - d, N);
                clear_point(out, x + d, N);
            }
        }

        // Each newly created difference blocks points around every old anchor.
        // Around x was already handled above.
        for (int d = 1; d <= N; ++d) {
            if (!((new_bits >> d) & Mask(1))) continue;
            for (int a : A) {
                clear_point(out, a - d, N);
                clear_point(out, a + d, N);
            }
        }

        // New symmetric/midpoint blockers involving x and an old element.
        for (int a : A) {
            int s = a + x;
            if ((s & 1) == 0) {
                clear_point(out, s / 2, N);
            }
        }

        return out;
    }

    bool leaf_symmetry_ok() {
        if (A.empty()) return true;
        return A.front() <= N + 1 - A.back();
    }

    bool dfs(int start, Mask diff_mask, Mask unblocked) {
        if ((stats.nodes & 0x3ffff) == 0 && time_exceeded()) {
            timed_out = true;
            return false;
        }
        ++stats.nodes;

        int need = K - static_cast<int>(A.size());
        int unblocked_count = popcount128(unblocked);
        if (unblocked_count > future_cap[static_cast<int>(A.size())]) {
            ++stats.coverage_prunes;
            return false;
        }

        if (need == 0) {
            ++stats.leaves;
            if (!leaf_symmetry_ok()) return false;
            if (unblocked == 0) {
                answer = A;
                return true;
            }
            return false;
        }
        if (N - start + 1 < need) return false;

        int local_last_start = N - need + 1;
        if (A.empty()) {
            int sym_cap = (N + 1) / 2;
            local_last_start = std::min(local_last_start, sym_cap);
        }

        struct Candidate {
            int unblock;
            int x;
            Mask bits;
            Mask next_unblocked;
        };
        std::vector<Candidate> candidates;
        candidates.reserve(N - start + 1);

        int j_after = static_cast<int>(A.size()) + 1;
        int future_after = future_cap[j_after];

        for (int x = start; x <= local_last_start; ++x) {
            Mask new_bits = 0;
            bool collide = false;
            for (int a : A) {
                int d = x - a;  // x > a since construction is increasing.
                Mask b = Mask(1) << d;
                if ((diff_mask | new_bits) & b) {
                    collide = true;
                    break;
                }
                new_bits |= b;
            }
            if (collide) {
                ++stats.sidon_prunes;
                continue;
            }

            Mask next_unblocked = update_unblocked(x, diff_mask, new_bits, unblocked);
            int u_after = popcount128(next_unblocked);
            if (u_after > future_after) {
                ++stats.coverage_prunes;
                continue;
            }
            candidates.push_back({u_after, x, new_bits, next_unblocked});
        }

        if (coverage_order) {
            std::sort(candidates.begin(), candidates.end(),
                      [](const Candidate& a, const Candidate& b) {
                          if (a.unblock != b.unblock) return a.unblock < b.unblock;
                          return a.x < b.x;
                      });
        }

        for (const auto& c : candidates) {
            A.push_back(c.x);
            if (dfs(c.x + 1, diff_mask | c.bits, c.next_unblocked)) return true;
            A.pop_back();
            if (timed_out) return false;
        }
        return false;
    }
};

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " N k [time_limit_s] [lex]\n";
        return 2;
    }
    int N = std::stoi(argv[1]);
    int K = std::stoi(argv[2]);
    double limit = (argc >= 4) ? std::stod(argv[3]) : 0.0;

    if (N >= 127) {
        std::cerr << "N must be <= 126 for the current unsigned __int128 mask.\n";
        return 2;
    }

    Search search(N, K, limit);
    if (argc >= 5 && std::string(argv[4]) == "lex") {
        search.coverage_order = false;
    }

    auto t0 = std::chrono::steady_clock::now();
    bool found = search.dfs(1, 0, search.initial_unblocked());
    auto t1 = std::chrono::steady_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();

    std::cout << "{\n";
    std::cout << "  \"N\": " << N << ",\n";
    std::cout << "  \"k\": " << K << ",\n";
    std::cout << "  \"status\": \""
              << (found ? "feasible" : (search.timed_out ? "timeout" : "infeasible"))
              << "\",\n";
    std::cout << "  \"time_s\": " << elapsed << ",\n";
    std::cout << "  \"nodes\": " << search.stats.nodes << ",\n";
    std::cout << "  \"leaves\": " << search.stats.leaves << ",\n";
    std::cout << "  \"sidon_prunes\": " << search.stats.sidon_prunes << ",\n";
    std::cout << "  \"coverage_prunes\": " << search.stats.coverage_prunes << ",\n";
    std::cout << "  \"A\": ";
    if (!found) {
        std::cout << "null\n";
    } else {
        std::cout << "[";
        for (size_t i = 0; i < search.answer.size(); ++i) {
            if (i) std::cout << ", ";
            std::cout << search.answer[i];
        }
        std::cout << "]\n";
    }
    std::cout << "}\n";
    return found ? 0 : (search.timed_out ? 1 : 0);
}
