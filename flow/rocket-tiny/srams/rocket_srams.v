// rocket_srams.v — SRAM-macro implementations of the Rocket memory arrays.
//
// Chipyard emits BEHAVIOURAL implementations of its `*_ext` memory modules
// (reg arrays, further split into byte lanes). Those synthesise to flip-flops:
// the 8 KiB scratchpad alone becomes ~65,000 of them, which dominates the
// design and is what made ABC grind for an hour. These replace the same module
// interfaces with sky130 SRAM macros.
//
// The fit is exact rather than lucky: TinyRocketConfig's arrays are 32 bits
// wide with byte write-enables, and sky130_sram_1kbyte_1rw1r_32x256_8 is 32
// bits wide with a 4-bit write mask. Only depth needs composing, by banking.
//
// Timing: Chipyard's model registers the ADDRESS and reads combinationally
// from it, giving one-cycle read latency. The macro is likewise one cycle. The
// output multiplexer therefore selects on the REGISTERED bank index, because
// read data returns the cycle after its address was presented.
//
// The macro's control polarity is active-LOW (csb0, web0); Rocket's is
// active-high (RW0_en, RW0_wmode).
//
// Not replaced: rockettile_icache_tag_array_0_ext (64 x 21). Its width does
// not match the 32-bit macro and it is only 1,344 bits — cheaper as flops than
// as a macro whose smallest instance is 8 Kib.

`ifndef ROCKET_SRAMS_V
`define ROCKET_SRAMS_V

// ---------------------------------------------------------------------------
// D-cache scratchpad: 2048 x 32 with byte mask  ->  8 banks of 256 x 32
// ---------------------------------------------------------------------------
module rockettile_dcache_data_arrays_0_ext(
  input  [10:0] RW0_addr,
  input         RW0_clk,
  input  [31:0] RW0_wdata,
  output [31:0] RW0_rdata,
  input         RW0_en,
  input         RW0_wmode,
  input  [3:0]  RW0_wmask
);
  localparam BANKS = 8;
  wire [2:0] bank = RW0_addr[10:8];
  wire [7:0] word = RW0_addr[7:0];

  // read data returns one cycle later, so the output mux uses the bank index
  // as it was when the address was presented
  reg [2:0] bank_q;
  always @(posedge RW0_clk) bank_q <= bank;

  wire [31:0] dout [0:BANKS-1];

  genvar i;
  generate
    for (i = 0; i < BANKS; i = i + 1) begin : b
      sky130_sram_1kbyte_1rw1r_32x256_8 macro (
        .clk0  (RW0_clk),
        .csb0  (~(RW0_en && (bank == i[2:0]))),   // active low
        .web0  (~RW0_wmode),                      // active low
        .wmask0(RW0_wmask),
        .addr0 (word),
        .din0  (RW0_wdata),
        .dout0 (dout[i]),
        // the second (read-only) port is unused by this array
        .clk1  (RW0_clk),
        .csb1  (1'b1),
        .addr1 (8'b0),
        .dout1 ()
      );
    end
  endgenerate

  assign RW0_rdata = dout[bank_q];
endmodule

// ---------------------------------------------------------------------------
// I-cache data: 512 x 32, unmasked  ->  2 banks of 256 x 32
// ---------------------------------------------------------------------------
module rockettile_icache_data_arrays_0_0_ext(
  input  [8:0]  RW0_addr,
  input         RW0_clk,
  input  [31:0] RW0_wdata,
  output [31:0] RW0_rdata,
  input         RW0_en,
  input         RW0_wmode
);
  wire       bank = RW0_addr[8];
  wire [7:0] word = RW0_addr[7:0];

  reg bank_q;
  always @(posedge RW0_clk) bank_q <= bank;

  wire [31:0] dout0_w, dout1_w;

  sky130_sram_1kbyte_1rw1r_32x256_8 macro0 (
    .clk0(RW0_clk), .csb0(~(RW0_en && ~bank)), .web0(~RW0_wmode),
    .wmask0(4'hF), .addr0(word), .din0(RW0_wdata), .dout0(dout0_w),
    .clk1(RW0_clk), .csb1(1'b1), .addr1(8'b0), .dout1()
  );
  sky130_sram_1kbyte_1rw1r_32x256_8 macro1 (
    .clk0(RW0_clk), .csb0(~(RW0_en &&  bank)), .web0(~RW0_wmode),
    .wmask0(4'hF), .addr0(word), .din0(RW0_wdata), .dout0(dout1_w),
    .clk1(RW0_clk), .csb1(1'b1), .addr1(8'b0), .dout1()
  );

  assign RW0_rdata = bank_q ? dout1_w : dout0_w;
endmodule

`endif
