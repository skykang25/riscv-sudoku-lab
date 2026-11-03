#!/usr/bin/env python3
"""Measure the solve interval using a real SIRVE debugger PTY session."""
import argparse
import os
import re
import shlex
import shutil
import sys
from pathlib import Path

import pexpect


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    executable = shutil.which("sirve")
    if not executable:
        parser.error("sirve must be on PATH")
    source = args.source.resolve()
    log = args.log.open("w", encoding="utf-8") if args.log else None
    stream = Tee(sys.stdout, log) if log else sys.stdout
    stream.write("SIRVE debugger measurement: " + source.name + "\n")
    stream.write("Command: sirve --asm " + shlex.quote(source.name) + "\n")
    stream.write("Break before solve at 0x90; break after jal solve at 0x28.\n\n")
    # A nested PTY has no independent cursor-query responder. TERM=dumb keeps
    # linenoise in its plain input mode; SIRVE's executed program is unchanged.
    child = pexpect.spawn(executable, ["--asm", str(source)],
                          encoding="utf-8", timeout=20, dimensions=(60, 140),
                          env={**os.environ, "TERM": "dumb"})
    child.logfile_read = stream
    try:
        child.expect_exact(">>")
        for command in ("ba0x90", "ba0x28"):
            child.sendline(command)
            child.expect_exact(">>")
        counters = []
        for _ in range(6):
            child.sendline("c")
            child.expect_exact(">>")
            match = re.search(r"\[inst:\s*(\d+) pc:\s*(\d+),", child.before)
            if not match:
                raise RuntimeError("No breakpoint counter in SIRVE output")
            counters.append(tuple(map(int, match.groups())))
        for index, (_, pc) in enumerate(counters):
            if pc != (0x90 if index % 2 == 0 else 0x28):
                raise RuntimeError("Source layout changed: verify addresses with 'l'")
        child.sendline("q")
        child.expect(pexpect.EOF)
        child.close()
        if child.exitstatus != 0:
            raise RuntimeError("SIRVE did not exit successfully")
        stream.write("\nPuzzle   Entry   Return   Dynamic instructions\n")
        for puzzle in range(3):
            entry = counters[2 * puzzle][0]
            returned = counters[2 * puzzle + 1][0]
            stream.write(f"{puzzle + 1:>6} {entry:>7} {returned:>8} {returned-entry:>22}\n")
        stream.write("Count = return counter - entry counter; this is not elapsed time.\n")
    finally:
        if child.isalive():
            child.close(force=True)
        if log:
            log.close()


if __name__ == "__main__":
    main()
