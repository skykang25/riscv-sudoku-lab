#!/usr/bin/env python3
"""Functional, helper-interface, trace, and calling-convention checks."""
import ctypes
import random
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIRVE = shutil.which("sirve")
NAMES = ("sudoku_baseline.s", "sudoku_bitmask.s")
SAVED = (8, 9, *range(18, 28))


def run(path, *options):
    result = subprocess.run([SIRVE, "--asm", str(path), *options],
                            text=True, capture_output=True, timeout=30, check=True)
    assert "Execution done!" in result.stdout, result.stdout[-1000:]
    return result.stdout


def outputs(text):
    return [int(value, 16) for value in
            re.findall(r"\[System output\]: (0x[0-9a-f]+)", text)]


def regions(source):
    before, editable = source.split("####### Modify this part! #############>>", 1)
    middle, after = editable.split("### Do not modify beyond this point! ##<<", 1)
    return before, middle, after


def oracle(board, p, digit):
    row, col = divmod(p, 4)
    peers = {row * 4 + c for c in range(4)}
    peers |= {r * 4 + col for r in range(4)}
    peers |= {r * 4 + c for r in range(row // 2 * 2, row // 2 * 2 + 2)
              for c in range(col // 2 * 2, col // 2 * 2 + 2)}
    return int(all(board[index] != digit for index in peers))


def transform(board, rows, cols, digits, transpose):
    return [digits[board[(cols[c] * 4 + rows[r]) if transpose
                         else (rows[r] * 4 + cols[c])]]
            for r in range(4) for c in range(4)]


def axis(rng):
    bands = [0, 1]
    rng.shuffle(bands)
    result = []
    for band in bands:
        pair = [2 * band, 2 * band + 1]
        rng.shuffle(pair)
        result.extend(pair)
    return result


def audit_trace(text, puzzles):
    regs = [0] * 32
    active = None
    puzzle = 0
    stores = []
    for line in text.splitlines():
        if not line.startswith("TRACE "):
            continue
        fields = dict(re.findall(r"(\w+)=(\S+)", line))
        pc = int(fields["pc"], 16)
        if pc == 0x90:
            assert active is None
            active = (regs[10], regs[2], regs[1], tuple(regs[i] for i in SAVED))
        if active:
            base, entry_sp, entry_ra, saved = active
            for operation in ("load", "store"):
                if operation not in fields:
                    continue
                address = int(fields[operation], 16)
                size = int(fields.get("size", "4")) if operation == "store" else 1
                in_board = base <= address and address + size <= base + 16
                in_stack = entry_sp - 28 <= address and address + size <= entry_sp
                assert in_board or in_stack, (pc, operation, address)
                if operation == "store" and in_board:
                    index = address - base
                    assert pc == 0x114 and size == 1
                    assert puzzles[puzzle][index] == 0, "Given clue was overwritten"
                    stores.append((puzzle, index, int(fields["value"], 16)))
        if "rd" in fields:
            regs[int(fields["rd"][1:])] = int(fields["value"], 16)
        if active and int(fields["next"], 16) == 0x28:
            base, entry_sp, entry_ra, saved = active
            assert regs[2] == entry_sp and regs[1] == entry_ra
            assert tuple(regs[i] for i in SAVED) == saved
            active = None
            puzzle += 1
    assert puzzle == 3 and active is None
    return stores


def main():
    assert SIRVE, "sirve must be on PATH"
    sources = [(ROOT / name).read_text() for name in NAMES]
    assert regions(sources[0])[::2] == regions(sources[1])[::2]
    assert (ROOT.parent / "sudoku1.s").read_text() == sources[0] if (ROOT.parent / "sudoku1.s").exists() else True
    public = [[int(n) for n in row.split()] for row in
              re.findall(r"^\.byte (.+)$", sources[0], re.M)]
    puzzles, solutions = public[:3], public[3:]
    traces = []
    for name in NAMES:
        text = run(ROOT / name, "--trace", "--max-instructions", "100000", "run")
        assert outputs(text) == [0, 0, 0]
        traces.append(audit_trace(text, puzzles))
    assert traces[0] == traces[1], "Fill order differs"
    assert traces[0][0] == (0, 3, 1)
    print("PASS: public boards, identical fill order, clues, access bounds, saved registers/sp")

    rng = random.Random(20233125)
    cases = []
    for _ in range(64):
        index = rng.randrange(3)
        rows, cols = axis(rng), axis(rng)
        permutation = rng.sample([1, 2, 3, 4], 4)
        digits = {0: 0, **dict(zip(range(1, 5), permutation))}
        transpose = bool(rng.randrange(2))
        cases.append((transform(puzzles[index], rows, cols, digits, transpose),
                      transform(solutions[index], rows, cols, digits, transpose)))
    cases.append((solutions[0][:], solutions[0][:]))
    almost = solutions[0][:]
    almost[15] = 0
    cases.append((almost, solutions[0][:]))

    with tempfile.TemporaryDirectory(prefix="sudoku-lab-verify-") as directory:
        temporary = Path(directory)
        library = temporary / "design.so"
        subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                        "-shared", "-fPIC", str(ROOT / "sudoku_design.c"), "-o", str(library)], check=True)
        c = ctypes.CDLL(str(library))
        array = ctypes.c_uint8 * 16
        c.solve.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
        c.solve.restype = None
        c.can_place.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_int, ctypes.c_int]
        c.can_place.restype = ctypes.c_int
        for board, answer in cases:
            copied = array(*board)
            c.solve(copied)
            assert list(copied) == answer
        data = "\n.data\ninputcnt:\n.word " + str(len(cases)) + "\ninputs:\n"
        data += "".join(".byte " + " ".join(map(str, board)) + "\n" for board, _ in cases)
        data += "answers:\n" + "".join(".byte " + " ".join(map(str, answer)) + "\n" for _, answer in cases)
        for name, source in zip(NAMES, sources):
            fixture = temporary / name
            fixture.write_text(source.split(".data", 1)[0] + data)
            assert outputs(run(fixture, "--max-instructions", "2000000", "run")) == [0] * len(cases)
        print(f"PASS: {len(cases)} additional boards in C and both assembly versions")

        records = []
        for board, _ in cases[:4]:
            for p in range(16):
                empty = board[:]
                empty[p] = 0
                for digit in range(1, 5):
                    expected = oracle(empty, p, digit)
                    copied = array(*empty)
                    assert c.can_place(copied, p, digit) == expected
                    assert list(copied) == empty
                    records.append((empty, p, digit, expected))
        harness = f""".text
start:
    li sp 0x10000
    la s0 cases
    li s1 {len(records)}
    li s2 0
helper_test_loop:
    add a0 s0 zero
    lw a1 16(s0)
    lw a2 20(s0)
    jal can_place
    lw t0 24(s0)
    beq a0 t0 helper_test_next
    addi s2 s2 1
helper_test_next:
    addi s0 s0 28
    addi s1 s1 -1
    bnez s1 helper_test_loop
    li t0 0x10000
    sw s2 0(t0)
    hcf
"""
        data = "\n.data\ncases:\n" + "".join(
            ".byte " + " ".join(map(str, board)) + f"\n.word {p} {digit} {expected}\n"
            for board, p, digit, expected in records)
        for name, source in zip(NAMES, sources):
            helper = "can_place:\n" + source.split("\ncan_place:\n", 1)[1].split("### Do not modify beyond", 1)[0]
            fixture = temporary / ("helper-" + name)
            fixture.write_text(harness + helper + data)
            text = run(fixture, "--trace", "--max-instructions", "200000", "run")
            assert outputs(text) == [0]
            stores = re.findall(r"store=(0x[0-9a-f]+)", text)
            assert stores == ["0x00010000"], "Helper wrote memory"
        print(f"PASS: {len(records)} standalone helper cases, including every cell and digit; no memory writes")
    print("All verification checks passed.")


if __name__ == "__main__":
    main()
