/* Independent exhaustive audit of the N=212 global AP-degree depth-24 cover. */

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { N = 212, DEPTH = 24, MAX_MASKS = 2048 };

typedef struct {
    int value;
    int degree;
    int center_distance2;
} candidate_t;

static int candidate_cmp(const void *left, const void *right) {
    const candidate_t *a = left;
    const candidate_t *b = right;
    if (a->degree != b->degree) return b->degree - a->degree;
    if (a->center_distance2 != b->center_distance2)
        return a->center_distance2 - b->center_distance2;
    return a->value - b->value;
}

static int mask_cmp(const void *left, const void *right) {
    uint32_t a = *(const uint32_t *)left;
    uint32_t b = *(const uint32_t *)right;
    int ac = __builtin_popcount(a);
    int bc = __builtin_popcount(b);
    if (ac != bc) return ac - bc;
    return (a > b) - (a < b);
}

static int is_endpoint(int value) { return value == 1 || value == N; }

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s SURVIVORS_TXT SUMMARY_JSON\n", argv[0]);
        return 2;
    }

    int degree[N + 1];
    int position[N + 1];
    candidate_t candidates[N - 2];
    int variables[DEPTH];
    uint32_t masks[MAX_MASKS];
    uint32_t kept[MAX_MASKS];
    memset(degree, 0, sizeof(degree));
    for (int value = 0; value <= N; ++value) position[value] = -1;

    for (int middle = 1; middle <= N; ++middle) {
        int max_difference = middle - 1 < N - middle ? middle - 1 : N - middle;
        for (int difference = 1; difference <= max_difference; ++difference) {
            ++degree[middle - difference];
            ++degree[middle];
            ++degree[middle + difference];
        }
    }

    int candidate_count = 0;
    for (int value = 2; value < N; ++value) {
        int distance2 = abs(2 * value - (N + 1));
        candidates[candidate_count++] = (candidate_t){value, degree[value], distance2};
    }
    qsort(candidates, candidate_count, sizeof(candidate_t), candidate_cmp);
    for (int index = 0; index < DEPTH; ++index) {
        variables[index] = candidates[index].value;
        position[variables[index]] = index;
    }

    int mask_count = 0;
    for (int middle = 1; middle <= N; ++middle) {
        int max_difference = middle - 1 < N - middle ? middle - 1 : N - middle;
        for (int difference = 1; difference <= max_difference; ++difference) {
            int triple[3] = {middle - difference, middle, middle + difference};
            uint32_t mask = 0;
            int covered = 1;
            for (int item = 0; item < 3; ++item) {
                int value = triple[item];
                if (position[value] >= 0)
                    mask |= UINT32_C(1) << position[value];
                else if (!is_endpoint(value))
                    covered = 0;
            }
            if (!covered) continue;
            if (mask == 0) {
                fprintf(stderr, "fixed endpoints contain a 3-AP\n");
                return 3;
            }
            int duplicate = 0;
            for (int index = 0; index < mask_count; ++index)
                if (masks[index] == mask) duplicate = 1;
            if (!duplicate) {
                if (mask_count == MAX_MASKS) return 4;
                masks[mask_count++] = mask;
            }
        }
    }

    qsort(masks, mask_count, sizeof(uint32_t), mask_cmp);
    int kept_count = 0;
    for (int index = 0; index < mask_count; ++index) {
        int redundant = 0;
        for (int prior = 0; prior < kept_count; ++prior)
            if ((kept[prior] & masks[index]) == kept[prior]) redundant = 1;
        if (!redundant) kept[kept_count++] = masks[index];
    }

    FILE *survivor_file = fopen(argv[1], "w");
    if (!survivor_file) {
        perror(argv[1]);
        return 5;
    }
    uint64_t survivor_count = 0;
    uint64_t survivor_sum = 0;
    uint32_t survivor_xor = 0;
    const uint32_t raw_count = UINT32_C(1) << DEPTH;
    for (uint32_t raw_id = 0; raw_id < raw_count; ++raw_id) {
        int forbidden = 0;
        for (int mask_index = 0; mask_index < kept_count; ++mask_index) {
            uint32_t mask = kept[mask_index];
            if ((raw_id & mask) == mask) {
                forbidden = 1;
                break;
            }
        }
        if (!forbidden) {
            fprintf(survivor_file, "%" PRIu32 "\n", raw_id);
            ++survivor_count;
            survivor_sum += raw_id;
            survivor_xor ^= raw_id;
        }
    }
    fclose(survivor_file);

    FILE *summary = fopen(argv[2], "w");
    if (!summary) {
        perror(argv[2]);
        return 5;
    }
    fprintf(summary, "{\n  \"N\": %d,\n  \"split_count\": %d,\n", N, DEPTH);
    fprintf(summary, "  \"split_variables\": [");
    for (int index = 0; index < DEPTH; ++index)
        fprintf(summary, "%s%d", index ? ", " : "", variables[index]);
    fprintf(summary, "],\n  \"forbidden_mask_count\": %d,\n", kept_count);
    fprintf(summary, "  \"raw_assignment_count\": %" PRIu32 ",\n", raw_count);
    fprintf(summary, "  \"survivor_count\": %" PRIu64 ",\n", survivor_count);
    fprintf(summary, "  \"survivor_id_sum\": %" PRIu64 ",\n", survivor_sum);
    fprintf(summary, "  \"survivor_id_xor\": %" PRIu32 "\n}\n", survivor_xor);
    fclose(summary);

    if (kept_count != 132 || survivor_count != 96847) {
        fprintf(stderr, "unexpected audit result: masks=%d survivors=%" PRIu64 "\n",
                kept_count, survivor_count);
        return 6;
    }
    return 0;
}
