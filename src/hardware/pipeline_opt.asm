; ------------------------------------------------------------------------------
; Instruction Pipeline Optimization for VisionAI-ClipsMaster
; 
; This file contains optimized assembly routines with carefully scheduled 
; instructions to maximize pipeline efficiency on modern CPUs.
; ------------------------------------------------------------------------------

section .text

; ------------------------------------------------------------------------------
; Matrix multiplication optimization with AVX2 instructions and pipeline scheduling
; 
; void matrix_mult_avx2(const float* A, const float* B, float* C, int M, int N, int K);
; 
; Parameters:
;   A - pointer to first matrix (MxK)
;   B - pointer to second matrix (KxN)
;   C - pointer to result matrix (MxN)
;   M - number of rows in A and C
;   N - number of columns in B and C
;   K - number of columns in A and rows in B
; 
; Register usage:
;   rdi - pointer to A
;   rsi - pointer to B
;   rdx - pointer to C
;   rcx - M
;   r8  - N
;   r9  - K
; ------------------------------------------------------------------------------

global matrix_mult_avx2
matrix_mult_avx2:
    push    rbp
    mov     rbp, rsp
    
    ; Save non-volatile registers
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    
    ; Set up loop counters and pointers
    mov     r10, rdi        ; r10 = A
    mov     r11, rsi        ; r11 = B
    mov     r12, rdx        ; r12 = C
    mov     r13, rcx        ; r13 = M
    mov     r14, r8         ; r14 = N
    mov     r15, r9         ; r15 = K
    
    ; Calculate strides
    mov     rax, r15
    shl     rax, 2          ; rax = K * sizeof(float)
    mov     rbx, r14
    shl     rbx, 2          ; rbx = N * sizeof(float)
    
    ; Loop over rows of A
    xor     r8, r8          ; i = 0
.loop_i:
    cmp     r8, r13
    jge     .end_loop_i
    
    ; Calculate pointer to row i of A
    mov     rdi, r8
    imul    rdi, rax        ; rdi = i * (K * sizeof(float))
    add     rdi, r10        ; rdi = A + i * (K * sizeof(float))
    
    ; Loop over columns of B
    xor     r9, r9          ; j = 0
.loop_j:
    cmp     r9, r14
    jge     .end_loop_j
    
    ; Calculate pointer to column j of C
    mov     rsi, r8
    imul    rsi, rbx        ; rsi = i * (N * sizeof(float))
    add     rsi, r12        ; rsi = C + i * (N * sizeof(float))
    add     rsi, r9
    shl     rsi, 2          ; rsi = C + i * (N * sizeof(float)) + j * sizeof(float)
    
    ; Initialize accumulator registers to zero
    vxorps  ymm0, ymm0, ymm0
    vxorps  ymm1, ymm1, ymm1
    vxorps  ymm2, ymm2, ymm2
    vxorps  ymm3, ymm3, ymm3
    
    ; Loop over K in blocks of 8 (for AVX2)
    xor     rcx, rcx        ; k = 0
.loop_k:
    cmp     rcx, r15
    jge     .end_loop_k
    
    ; Calculate pointers for this iteration
    mov     rdx, rcx
    shl     rdx, 2          ; rdx = k * sizeof(float)
    
    lea     r12, [rdi + rdx]         ; r12 = A + i*(K*4) + k*4
    
    mov     rbx, rcx
    imul    rbx, rbx        ; rbx = k * (N * sizeof(float))
    add     rbx, r11        ; rbx = B + k * (N * sizeof(float))
    lea     rbx, [rbx + r9*4]       ; rbx = B + k*(N*4) + j*4
    
    ; Load data with 2 instruction gap for pipeline efficiency
    vmovaps ymm4, [r12]              ; Load 8 floats from A
    
    ; Insert pipeline bubble for load latency
    nop
    nop
    
    vmovaps ymm5, [rbx]              ; Load 8 floats from B
    
    ; Multiply and accumulate with pipeline scheduling
    vmulps  ymm6, ymm4, ymm5         ; Multiply A and B elements
    vaddps  ymm0, ymm0, ymm6         ; Accumulate to sum
    
    ; Advance pointers for next iteration
    add     rcx, 8          ; Process 8 elements at a time
    jmp     .loop_k
    
.end_loop_k:
    ; Horizontal sum of ymm0 register
    vextractf128 xmm1, ymm0, 1       ; Extract high 128 bits
    vaddps  xmm0, xmm0, xmm1         ; Add high 128 bits to low 128 bits
    
    ; Horizontal sum of 128 bits
    vshufps xmm1, xmm0, xmm0, 0x0E   ; Shuffle to get [3,2,3,2]
    vaddps  xmm0, xmm0, xmm1         ; Add to get [0+2,1+3,0+2,1+3]
    vshufps xmm1, xmm0, xmm0, 0x01   ; Shuffle to get [1,0,1,0]
    vaddps  xmm0, xmm0, xmm1         ; Add to get [0+1+2+3,0+1+2+3,0+1+2+3,0+1+2+3]
    
    ; Store result to C
    vmovss  [rsi], xmm0
    
    inc     r9
    jmp     .loop_j
    
.end_loop_j:
    inc     r8
    jmp     .loop_i
    
.end_loop_i:
    ; Restore non-volatile registers
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    
    pop     rbp
    ret

; ------------------------------------------------------------------------------
; Optimized Vector Dot Product with AVX2 and pipeline scheduling
; 
; float vector_dot_product_avx2(const float* A, const float* B, int size);
; 
; Parameters:
;   A    - pointer to first vector
;   B    - pointer to second vector
;   size - number of elements
; 
; Register usage:
;   rdi - pointer to A
;   rsi - pointer to B
;   rdx - size
; ------------------------------------------------------------------------------

global vector_dot_product_avx2
vector_dot_product_avx2:
    push    rbp
    mov     rbp, rsp
    
    ; Initialize accumulator registers to zero
    vxorps  ymm0, ymm0, ymm0
    vxorps  ymm1, ymm1, ymm1
    vxorps  ymm2, ymm2, ymm2
    vxorps  ymm3, ymm3, ymm3
    
    ; Calculate number of 32-element blocks (8 floats per ymm register × 4 accumulators)
    mov     rax, rdx
    shr     rax, 5          ; rax = size / 32
    
    ; If size < 32, skip the main loop
    test    rax, rax
    jz      .remainder
    
    ; Process 32 elements per iteration (8 floats × 4 accumulators)
.loop:
    ; Load from A, staggered to optimize pipeline
    vmovaps ymm4, [rdi]
    vmovaps ymm5, [rdi + 32]
    
    ; Load from B, with spacing for pipeline optimization
    vmovaps ymm6, [rsi]
    vmovaps ymm7, [rsi + 32]
    
    ; Perform multiplications and accumulate
    vmulps  ymm8, ymm4, ymm6
    vaddps  ymm0, ymm0, ymm8
    
    vmulps  ymm9, ymm5, ymm7
    vaddps  ymm1, ymm1, ymm9
    
    ; Load next data
    vmovaps ymm4, [rdi + 64]
    vmovaps ymm5, [rdi + 96]
    vmovaps ymm6, [rsi + 64]
    vmovaps ymm7, [rsi + 96]
    
    ; Perform multiplications and accumulate
    vmulps  ymm8, ymm4, ymm6
    vaddps  ymm2, ymm2, ymm8
    
    vmulps  ymm9, ymm5, ymm7
    vaddps  ymm3, ymm3, ymm9
    
    ; Update pointers
    add     rdi, 128
    add     rsi, 128
    
    ; Decrement counter and loop
    dec     rax
    jnz     .loop
    
    ; Combine the four accumulators
    vaddps  ymm0, ymm0, ymm1
    vaddps  ymm2, ymm2, ymm3
    vaddps  ymm0, ymm0, ymm2
    
.remainder:
    ; Handle the remainder elements (size % 32)
    mov     rcx, rdx
    and     rcx, 31         ; rcx = size % 32
    
    ; If no remainder, skip
    test    rcx, rcx
    jz      .finish
    
    ; Process remaining elements 8 at a time
    shr     rcx, 3          ; rcx = (size % 32) / 8
    test    rcx, rcx
    jz      .last_elements
    
.remainder_loop:
    ; Load 8 elements from A and B
    vmovaps ymm4, [rdi]
    vmovaps ymm5, [rsi]
    
    ; Multiply and accumulate
    vmulps  ymm6, ymm4, ymm5
    vaddps  ymm0, ymm0, ymm6
    
    ; Update pointers
    add     rdi, 32
    add     rsi, 32
    
    ; Decrement counter and loop
    dec     rcx
    jnz     .remainder_loop
    
.last_elements:
    ; Handle the very last elements (size % 8)
    mov     rcx, rdx
    and     rcx, 7          ; rcx = size % 8
    
    ; If no elements left, skip
    test    rcx, rcx
    jz      .finish
    
    ; Process last elements one at a time
.last_loop:
    ; Load single float from A and B
    vmovss  xmm4, [rdi]
    vmovss  xmm5, [rsi]
    
    ; Multiply and accumulate
    vmulss  xmm6, xmm4, xmm5
    vaddss  xmm1, xmm1, xmm6
    
    ; Update pointers
    add     rdi, 4
    add     rsi, 4
    
    ; Decrement counter and loop
    dec     rcx
    jnz     .last_loop
    
    ; Add the last elements to the main accumulator
    vextractf128 xmm2, ymm0, 1
    vaddps  xmm0, xmm0, xmm2
    vaddss  xmm0, xmm0, xmm1
    
.finish:
    ; Horizontal sum of ymm0 to get final result
    vextractf128 xmm1, ymm0, 1       ; Extract high 128 bits
    vaddps  xmm0, xmm0, xmm1         ; Add high 128 bits to low 128 bits
    
    ; Horizontal sum of 128 bits
    vshufps xmm1, xmm0, xmm0, 0x0E   ; Shuffle to get [3,2,3,2]
    vaddps  xmm0, xmm0, xmm1         ; Add to get [0+2,1+3,0+2,1+3]
    vshufps xmm1, xmm0, xmm0, 0x01   ; Shuffle to get [1,0,1,0]
    vaddps  xmm0, xmm0, xmm1         ; Add to get [0+1+2+3,0+1+2+3,0+1+2+3,0+1+2+3]
    
    ; Result is in xmm0 (scalar float)
    pop     rbp
    ret

; ------------------------------------------------------------------------------
; Simple Matrix-Vector Multiplication with AVX2 and pipeline scheduling 
;
; void matrix_vector_mult_avx2(const float* A, const float* x, float* y, int rows, int cols);
;
; Parameters:
;   A    - pointer to matrix (rows x cols)
;   x    - pointer to input vector (cols)
;   y    - pointer to output vector (rows)
;   rows - number of rows in matrix A
;   cols - number of columns in matrix A
; ------------------------------------------------------------------------------

global matrix_vector_mult_avx2
matrix_vector_mult_avx2:
    push    rbp
    mov     rbp, rsp
    
    ; Save non-volatile registers
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    
    ; r12 = A, r13 = x, r14 = y, r15 = rows, rbx = cols
    mov     r12, rdi
    mov     r13, rsi
    mov     r14, rdx
    mov     r15, rcx
    mov     rbx, r8
    
    ; For each row of A
    xor     rdi, rdi        ; row = 0
.loop_row:
    cmp     rdi, r15
    jge     .end_rows
    
    ; Initialize accumulator to zero
    vxorps  ymm0, ymm0, ymm0
    
    ; Calculate pointer to row
    mov     rax, rdi
    imul    rax, rbx        ; rax = row * cols
    shl     rax, 2          ; rax = row * cols * sizeof(float)
    add     rax, r12        ; rax = A + row * cols * sizeof(float)
    
    ; For each column of A, process in blocks of 8
    xor     rsi, rsi        ; col = 0
.loop_col:
    add     rsi, 8
    cmp     rsi, rbx
    jg      .remainder_cols
    
    ; Load 8 elements from A (current row)
    vmovaps ymm1, [rax + rsi*4 - 32]
    
    ; Insert pipeline bubbles for better scheduling
    nop
    nop
    
    ; Load 8 elements from x
    vmovaps ymm2, [r13 + rsi*4 - 32]
    
    ; Multiply and accumulate
    vmulps  ymm3, ymm1, ymm2
    vaddps  ymm0, ymm0, ymm3
    
    jmp     .loop_col
    
.remainder_cols:
    ; Process remaining columns (< 8)
    sub     rsi, 8
    
.loop_rem:
    cmp     rsi, rbx
    jge     .end_cols
    
    ; Load single element from A and x
    vmovss  xmm1, [rax + rsi*4]
    vmovss  xmm2, [r13 + rsi*4]
    
    ; Multiply and accumulate
    vmulss  xmm3, xmm1, xmm2
    vaddss  xmm0, xmm0, xmm3
    
    inc     rsi
    jmp     .loop_rem
    
.end_cols:
    ; Horizontal sum of ymm0
    vextractf128 xmm1, ymm0, 1
    vaddps  xmm0, xmm0, xmm1
    vhaddps xmm0, xmm0, xmm0
    vhaddps xmm0, xmm0, xmm0
    
    ; Store result to y
    vmovss  [r14 + rdi*4], xmm0
    
    inc     rdi
    jmp     .loop_row
    
.end_rows:
    ; Restore non-volatile registers
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    
    pop     rbp
    ret 