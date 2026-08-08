/* Bare-metal hello for TinyRocketConfig: UART TX + tohost exit.
   Linked at the DTIM (0x8000_0000); loaded by SimTSI over serial-TL. */
#define UART_BASE 0x10020000u
#define UART_TXDATA (*(volatile unsigned int *)(UART_BASE + 0x00))
#define UART_TXCTRL (*(volatile unsigned int *)(UART_BASE + 0x08))
#define UART_DIV    (*(volatile unsigned int *)(UART_BASE + 0x18))

volatile unsigned long long tohost __attribute__((section(".tohost"), aligned(64)));
volatile unsigned long long fromhost __attribute__((section(".tohost"), aligned(64)));

static void putc_(char c) {
  while (UART_TXDATA & 0x80000000u) ;   /* txdata.full */
  UART_TXDATA = (unsigned char)c;
}

void main(void) {

  UART_TXCTRL = 1;        /* txen */
  const char *s = "hello from rocket\n";
  for (; *s; s++) putc_(*s);
  /* drain: wait until the FIFO reports empty long enough for the last stop bit */
  for (volatile int i = 0; i < 400000; i++) ;
  tohost = 1;             /* riscv-tests pass code */
  for (;;) ;
}
