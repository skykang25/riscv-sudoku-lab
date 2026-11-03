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

# Return 1 exactly when candidate a2 is absent from the row, column, and box.
# This leaf function changes only caller-saved a/t registers and never the board.
can_place:
	add a3 a0 zero       # a3: board base
	add a4 a1 zero       # a4: cell index
	add a5 a2 zero       # a5: candidate digit

	# Check the four cells in the same row.
	andi t0 a4 -4        # first index of the row
	addi t1 zero 0
can_place_row_loop:
	li t4 4
	bge t1 t4 can_place_column_start
	add t2 t0 t1
	add t2 a3 t2
	lbu t3 0(t2)
	beq t3 a5 can_place_no
	addi t1 t1 1
	j can_place_row_loop

	# Check the four cells in the same column.
can_place_column_start:
	andi t0 a4 3         # column number
	addi t1 zero 0       # row offset: 0, 4, 8, 12
can_place_column_loop:
	li t4 16
	bge t1 t4 can_place_box_start
	add t2 t0 t1
	add t2 a3 t2
	lbu t3 0(t2)
	beq t3 a5 can_place_no
	addi t1 t1 4
	j can_place_column_loop

	# Box base is (p & 8) + (p & 2). Check its four cells.
can_place_box_start:
	andi t0 a4 8
	andi t1 a4 2
	add t0 t0 t1
	add t2 a3 t0
	lbu t3 0(t2)
	beq t3 a5 can_place_no
	lbu t3 1(t2)
	beq t3 a5 can_place_no
	lbu t3 4(t2)
	beq t3 a5 can_place_no
	lbu t3 5(t2)
	beq t3 a5 can_place_no

	li a0 1
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
