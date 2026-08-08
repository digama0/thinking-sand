/* Pure-compute co-sim test: exercises RV32IMAC (add/sub/mul/div/rem/shift/
   branch/load/store) with no MMIO, then exits via tohost. Every committed
   instruction is checkable against the golden model — no device reads to
   diverge on. */
volatile unsigned long long tohost __attribute__((section(".tohost"), aligned(64)));
volatile unsigned long long fromhost __attribute__((section(".tohost"), aligned(64)));

static unsigned buf[64];

unsigned compute(void) {
  unsigned acc = 0x12345678u;
  for (unsigned i = 1; i < 64; i++) {
    unsigned x = acc * 2654435761u;      /* M: mul */
    x ^= x >> 15;                        /* shift */
    x += i * i;                          /* mul */
    if (x & 1) x = (x << 3) | (x >> 29); /* rotate */
    unsigned q = x / (i + 1);            /* M: div */
    unsigned r = x % (i + 3);            /* M: rem */
    buf[i] = q ^ r;                      /* store */
    acc = acc + buf[i] - buf[i - 1];     /* load + arith */
  }
  unsigned sum = 0;
  for (unsigned i = 0; i < 64; i++) sum += buf[i];  /* load loop */
  return sum ^ acc;
}

void main(void) {
  unsigned result = compute();
  /* park the result where a debugger/host could read it; then pass. */
  buf[0] = result;
  tohost = 1;      /* riscv-tests pass */
  for (;;) ;
}
