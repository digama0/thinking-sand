ENTRY(_start)
SECTIONS {
  . = 0x80000000;
  .text : { *(.text.start) *(.text*) }
  .rodata : { *(.rodata*) *(.srodata*) }
  .data : { *(.data*) *(.sdata*) }
  .tohost ALIGN(64) : { *(.tohost) }
  .bss : { *(.bss*) *(.sbss*) }
  . = ALIGN(16);
  . += 1024;
  _stack_top = .;
}
