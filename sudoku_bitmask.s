.text 
start:
	li sp 0x10000
	la s0 inputcnt
	lw s0 0(s0)
	la s5 inputs

input_loop:
	add a0 s5 zero
	addi a1 zero 0
	jal solve

	addi s5 s5 16
	addi s0 s0 -1
	bnez s0 input_loop

	la s0 inputcnt
	lw s0 0(s0)
	la s1 inputs
	la s2 answers
loop_answers:
	li s3 16
	addi s4 zero 0

	loop_answer:
		lb t2 0(s1)
		lb t3 0(s2)
		beq t2 t3 skip_different

		addi s4 s4 1

		skip_different:
		addi s1 s1 1
		addi s2 s2 1
		addi s3 s3 -1
		bnez s3 loop_answer

	li t4 0x10000
	sw s4 0(t4)

	addi s0 s0 -1
	bnez s0 loop_answers
	hcf

#########################################
####### Modify this part! #############>>

solve:
	# Stack frame (28 bytes): ra, s0-s5.
	addi sp sp -28
	sw ra 24(sp)
	sw s0 20(sp)
	sw s1 16(sp)
	sw s2 12(sp)
	sw s3 8(sp)
	sw s4 4(sp)
	sw s5 0(sp)

	add s0 a0 zero       # s0: board base address

solve_repeat:
	addi s1 zero 0       # s1: changes in this pass
	addi s2 zero 0       # s2: current cell index p

solve_cell_loop:
	li t0 16 			#t0: break 조건
	bge s2 t0 solve_pass_done	#인덱스 s2가 16이랑 같아지면, 탈출
	add t0 s0 s2			
	lbu t1 0(t0)
	bnez t1 solve_next_cell		#0번째 인덱스 값에 비어있는지 없는지 확인

	addi s3 zero 1       # s3: candidate digit (1..4)
	addi s4 zero 0       # s4: legal candidate count
	addi s5 zero 0       # s5: last legal candidate

solve_candidate_loop:
	li t0 5
	bge s3 t0 solve_candidates_done
	add a0 s0 zero
	add a1 s2 zero
	add a2 s3 zero
	jal can_place
	beqz a0 solve_next_candidate
	addi s4 s4 1
	add s5 s3 zero

solve_next_candidate:
	addi s3 s3 1
	j solve_candidate_loop

solve_candidates_done:
	li t0 1
	bne s4 t0 solve_next_cell
	add t0 s0 s2
	sb s5 0(t0)
	addi s1 s1 1

solve_next_cell:
	addi s2 s2 1
	j solve_cell_loop

solve_pass_done:
	bnez s1 solve_repeat

	lw s5 0(sp)
	lw s4 4(sp)
	lw s3 8(sp)
	lw s2 12(sp)
	lw s1 16(sp)
	lw s0 20(sp)
	lw ra 24(sp)
	addi sp sp 28
	ret

# Each bit (1 << digit) records a digit present in the checked cells.
# Keep the required independent (board, index, digit) -> boolean interface.
# Only caller-saved registers are used; no persistent state or extra memory.
can_place:
	li t6 1
	sll t0 t6 a2        # t0: candidate bit; t6: constant 1

	# Build the row mask from four byte loads (the target cell is zero).
	andi t1 a1 -4
	add t1 a0 t1
	lbu t2 0(t1)
	lbu t3 1(t1)
	lbu t4 2(t1)
	lbu t5 3(t1)
	sll t2 t6 t2
	sll t3 t6 t3
	sll t4 t6 t4
	sll t5 t6 t5
	or t2 t2 t3
	or t2 t2 t4
	or t2 t2 t5
	and t2 t2 t0
	bnez t2 can_place_no

	# Build the column mask from offsets 0, 4, 8, 12.
	andi t1 a1 3
	add t1 a0 t1
	lbu t2 0(t1)
	lbu t3 4(t1)
	lbu t4 8(t1)
	lbu t5 12(t1)
	sll t2 t6 t2
	sll t3 t6 t3
	sll t4 t6 t4
	sll t5 t6 t5
	or t2 t2 t3
	or t2 t2 t4
	or t2 t2 t5
	and t2 t2 t0
	bnez t2 can_place_no

	# In a 2x2 box, row/column checks already covered three of its cells.
	# The remaining diagonal peer has index p XOR 5 (toggle row bit 0
	# and column bit 0). This formula is specific to a 4x4 board.
	xori t1 a1 5
	add t1 a0 t1
	lbu t2 0(t1)
	sll t2 t6 t2
	and t2 t2 t0
	sltiu a0 t2 1      # 1 if the candidate bit is absent, otherwise 0
	ret

can_place_no:
	addi a0 zero 0
	ret

### Do not modify beyond this point! ##<<
#########################################


.data
inputcnt:
.word 3
inputs: 
.byte 0 4 3 0 0 0 4 2 0 2 0 0 3 0 0 0
.byte 0 0 3 0 0 4 0 2 0 0 2 0 0 2 0 3
.byte 0 3 0 4 0 0 2 0 4 0 3 0 0 0 0 2

answers:
.byte 2 4 3 1 1 3 4 2 4 2 1 3 3 1 2 4 
.byte 2 1 3 4 3 4 1 2 4 3 2 1 1 2 4 3 
.byte 2 3 1 4 1 4 2 3 4 2 3 1 3 1 4 2 
