// Exact fixed-size search for Erdos Problem #156.
//
// Build:
//   clang++ -O3 -std=c++17 erdos_156/search156.cpp -o erdos_156/search156
//
// Usage:
//   erdos_156/search156 70 6 300
//
// The third argument is an optional wall-clock time limit in seconds.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using Mask = unsigned __int128;

struct Stats {
    unsigned long long nodes = 0;
    unsigned long long leaves = 0;
    unsigned long long sidon_prunes = 0;
};

struct Search {
    int N;
    int K;
    double limit_s;
    std::chrono::steady_clock::time_point start_time;
    Stats stats;
    std::vector<int> A;
    std::vector<int> answer;
    bool timed_out = false;
    bool coverage_order = true;

    Search(int n, int k, double limit)
        : N(n), K(k), limit_s(limit), start_time(std::chrono::steady_clock::now()) {
        A.reserve(K);
    }

    bool time_exceeded() {
        if (limit_s <= 0) return false;
        auto now = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double>(now - start_time).count();
        return elapsed > limit_s;
    }

    static bool bit(Mask m, int d) {
        return (m >> d) & Mask(1);
    }

    int blocked_count(Mask diff_mask) {
        int count = 0;
        for (int x = 1; x <= N; ++x) {
            if (is_blocked_or_in_A(x, diff_mask)) ++count;
        }
        return count;
    }

    bool is_blocked_or_in_A(int x, Mask diff_mask) {
        Mask new_bits = 0;
        for (int a : A) {
            int d = std::abs(x - a);
            if (d == 0) return true;
            Mask b = Mask(1) << d;
            if ((diff_mask | new_bits) & b) return true;
            new_bits |= b;
        }
        return false;
    }

    bool is_maximal(Mask diff_mask) {
        for (int x = 1; x <= N; ++x) {
            if (!is_blocked_or_in_A(x, diff_mask)) return false;
        }
        return true;
    }

    bool leaf_symmetry_ok() {
        if (A.empty()) return true;
        return A.front() <= N + 1 - A.back();
    }

    bool dfs(int start, Mask diff_mask) {
        if ((stats.nodes & 0x3ffff) == 0 && time_exceeded()) {
            timed_out = true;
            return false;
        }
        ++stats.nodes;

        int need = K - static_cast<int>(A.size());
        if (need == 0) {
            ++stats.leaves;
            if (!leaf_symmetry_ok()) return false;
            if (is_maximal(diff_mask)) {
                answer = A;
                return true;
            }
            return false;
        }
        if (N - start + 1 < need) return false;

        struct Candidate {
            int score;
            int x;
            Mask bits;
        };
        std::vector<Candidate> candidates;
        candidates.reserve(N - start + 1);

        int last_start = N - need + 1;
        for (int x = start; x <= last_start; ++x) {
            Mask new_bits = 0;
            bool collide = false;
            for (int a : A) {
                int d = x - a;  // x is always greater than existing a.
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
            int score = 0;
            if (coverage_order) {
                A.push_back(x);
                score = 1000 * blocked_count(diff_mask | new_bits);
                score += A.back() - A.front();
                A.pop_back();
            }
            candidates.push_back({score, x, new_bits});
        }

        if (coverage_order) {
            std::sort(candidates.begin(), candidates.end(),
                      [](const Candidate& a, const Candidate& b) {
                          if (a.score != b.score) return a.score > b.score;
                          return a.x > b.x;
                      });
        }

        for (const auto& c : candidates) {
            A.push_back(c.x);
            if (dfs(c.x + 1, diff_mask | c.bits)) return true;
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

    Search search(N, K, limit);
    if (argc >= 5 && std::string(argv[4]) == "lex") {
        search.coverage_order = false;
    }

    auto t0 = std::chrono::steady_clock::now();
    bool found = search.dfs(1, 0);
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
