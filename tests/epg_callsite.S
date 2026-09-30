.text
.p2align 2
.globl _testEPGPop
_testEPGPop:
    .cfi_startproc
#if defined(__arm64__)
    stp x29, x30, [sp, #-16]!
    .cfi_def_cfa_offset 16
    .cfi_offset x29, -16
    .cfi_offset x30, -8
    mov x29, sp
    .cfi_def_cfa_register x29
    mov x2, #0
    bl _objc_msgSend
Lreturn:
    ldp x29, x30, [sp], #16
    .cfi_def_cfa sp, 0
    ret
#elif defined(__x86_64__)
    pushq %rbp
    .cfi_def_cfa_offset 16
    .cfi_offset %rbp, -16
    movq %rsp, %rbp
    .cfi_def_cfa_register %rbp
    xorl %edx, %edx
    callq _objc_msgSend
Lreturn:
    popq %rbp
    .cfi_def_cfa %rsp, 8
    retq
#endif
    .cfi_endproc
.globl _testEPGReturnAddress
.set _testEPGReturnAddress, Lreturn
