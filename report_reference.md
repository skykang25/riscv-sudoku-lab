# 보고서 (c)에 넣을 참조 문구

아래 본문은 보고서 공간에 맞춰 줄여 사용할 수 있습니다. 기존 (a)·(b)의 캡처와
(c)의 기본 측정값은 `sudoku_baseline.s`를 기준으로 하고, 개선 후 결과는 추가 비교로 표시합니다.

> 추가 비교를 위해 `can_place`에 로컬 비트마스크, 고정 길이 반복문의 펼치기,
> 행·열과 중복되는 박스 검사 제거를 적용하였다. 동일한 중단점 구간에서 측정한
> 세 퍼즐의 동적 명령어 수는 각각 3004→2092, 3766→2458, 3355→2260으로 감소하였다.
> 합계는 10125→6810으로 32.74% 감소했으며, 두 구현 모두 세 퍼즐의 불일치 수가 0이었다.
> 이 수치는 세 변경을 함께 적용한 결과이고 실행 시간 측정값은 아니다.
> 개선 전후 소스, C 설계 모델, 실제 터미널 측정 화면과 원본 로그는 참고자료 [1]에 수록하였다.

| 퍼즐 | 개선 전 | 개선 후 | 감소율 |
|---|---:|---:|---:|
| 1 | 3004 | 2092 | 30.36% |
| 2 | 3766 | 2458 | 34.73% |
| 3 | 3355 | 2260 | 32.64% |

## 참고자료

[1] 강동흔, *RISC-V Sudoku Lab*, 소스·실행 증거 고정 버전
`2a8daa271c4a269938b75edef8e5825bb5a07ed2`.
https://github.com/skykang25/riscv-sudoku-lab/tree/2a8daa271c4a269938b75edef8e5825bb5a07ed2

개별 자료의 고정 링크:

- [개선 전 assembly](https://github.com/skykang25/riscv-sudoku-lab/blob/2a8daa271c4a269938b75edef8e5825bb5a07ed2/sudoku_baseline.s)
- [C 설계 모델](https://github.com/skykang25/riscv-sudoku-lab/blob/2a8daa271c4a269938b75edef8e5825bb5a07ed2/sudoku_design.c)
- [개선 후 assembly](https://github.com/skykang25/riscv-sudoku-lab/blob/2a8daa271c4a269938b75edef8e5825bb5a07ed2/sudoku_bitmask.s)
- [비교 표·캡처·재현 방법](https://github.com/skykang25/riscv-sudoku-lab/blob/2a8daa271c4a269938b75edef8e5825bb5a07ed2/README.md)

GitHub 링크는 코드와 추가 증거의 참조입니다. 보고서 본문에는 과제에서 요구하는
기본 측정표와 software/ISA 개선 제안의 짧은 설명을 남겨야 합니다.
현재 개선 assembly는 RV32I만 사용합니다. `cpop`·`ctz` 등을 활용하는 ISA 확장 제안은
별도 제안이며 이 비교본에 구현한 기능이 아닙니다.
