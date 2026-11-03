#include <stdint.h>

/* C design model corresponding to the baseline assembly.
 * board[p] is a byte, p is 0..15, and digit is 1..4.
 * The requested cell is assumed to be empty.
 */
int can_place(const uint8_t board[16], int p, int digit)
{
    int row = p / 4;
    int col = p % 4;

    for (int c = 0; c < 4; c++) {
        if (board[row * 4 + c] == digit)
            return 0;
    }

    for (int r = 0; r < 4; r++) {
        if (board[r * 4 + col] == digit)
            return 0;
    }

    int box_row = (row / 2) * 2;
    int box_col = (col / 2) * 2;
    for (int r = box_row; r < box_row + 2; r++) {
        for (int c = box_col; c < box_col + 2; c++) {
            if (board[r * 4 + c] == digit)
                return 0;
        }
    }
    return 1;
}

void solve(uint8_t board[16])
{
    int changes;
    do {
        changes = 0;
        for (int p = 0; p < 16; p++) {
            if (board[p] != 0)
                continue;

            int count = 0;
            int last = 0;
            for (int digit = 1; digit <= 4; digit++) {
                if (can_place(board, p, digit)) {
                    count++;
                    last = digit;
                }
            }
            if (count == 1) {
                board[p] = (uint8_t)last;
                changes++;
            }
        }
    } while (changes != 0);
}

#ifdef SUDOKU_DEMO
#include <stdio.h>
#include <string.h>

int main(void)
{
    uint8_t boards[3][16] = {
        {0,4,3,0, 0,0,4,2, 0,2,0,0, 3,0,0,0},
        {0,0,3,0, 0,4,0,2, 0,0,2,0, 0,2,0,3},
        {0,3,0,4, 0,0,2,0, 4,0,3,0, 0,0,0,2}
    };
    const uint8_t expected[3][16] = {
        {2,4,3,1, 1,3,4,2, 4,2,1,3, 3,1,2,4},
        {2,1,3,4, 3,4,1,2, 4,3,2,1, 1,2,4,3},
        {2,3,1,4, 1,4,2,3, 4,2,3,1, 3,1,4,2}
    };
    int failed = 0;
    for (int puzzle = 0; puzzle < 3; puzzle++) {
        solve(boards[puzzle]);
        int mismatches = 0;
        for (int p = 0; p < 16; p++)
            mismatches += boards[puzzle][p] != expected[puzzle][p];
        printf("Puzzle %d: mismatched cells = %d\n", puzzle + 1, mismatches);
        failed |= mismatches != 0;
    }
    return failed;
}
#endif
