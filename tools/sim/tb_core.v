// tb_core.v — run the SHIPPED core on a REAL firmware image and check the
// L5/04 Wishbone guarantee clauses on the resulting traces.
//
// This is the first thing in the project that actually EXECUTES the design.
// It is deliberately minimal: the core, a memory that answers both Wishbone
// masters, and monitors. No SoC fabric — the fabric's decode is already
// checked statically (L7/memmap), and what L5/04 needs is the CORE's bus
// discipline, which is a property of the core alone.
//
// Memory model: flash at 0x10000000 (loaded from the built image, read-only,
// the XIP region the reset vector targets) and RAM at 0x00000000 (the dff
// region the linker puts .data/.bss/stack in). Both answer with a
// parameterisable latency so the checks see multi-cycle transactions rather
// than a degenerate always-ready bus.
//
// The clauses checked (L5/04's Gi1-3 / Gd1-3, as run-time assertions):
//   G1  STB implies CYC              (no strobe outside a cycle)
//   G2  a request holds ADR/WE/SEL stable until ACK  (no mid-transaction change)
//   G3  every cycle terminates       (no request outlives the timeout)
//   G4  the instruction bus never writes (iBus WE is constant 0)
// Violations print `VIOLATION:` and set a failure flag; tools/simcheck.py
// greps for that and for the end-of-run summary.
`timescale 1ns/1ps

module tb_core;
   parameter MEM_LAT   = 2;          // wait states before ACK
   parameter MAX_CYCLES = 200000;
   parameter FLASH_BASE = 32'h10000000;
   parameter FLASH_WORDS = 4096;
   parameter RAM_WORDS   = 512;      // dff + dff2 = 0x600 bytes

   reg clk = 0, reset = 1;
   always #5 clk = ~clk;

   // ---- the core -----------------------------------------------------------
   wire        iCYC, iSTB, iWE;  wire [29:0] iADR;  wire [3:0] iSEL;
   wire [31:0] iMOSI;            reg  [31:0] iMISO; reg iACK = 0;
   wire        dCYC, dSTB, dWE;  wire [29:0] dADR;  wire [3:0] dSEL;
   wire [31:0] dMOSI;            reg  [31:0] dMISO; reg dACK = 0;

   VexRiscv core (
      .externalResetVector(FLASH_BASE),
      .timerInterrupt(1'b0), .softwareInterrupt(1'b0),
      .externalInterruptArray(32'b0),
      .debug_bus_cmd_valid(1'b0), .debug_bus_cmd_payload_wr(1'b0),
      .debug_bus_cmd_payload_address(8'b0), .debug_bus_cmd_payload_data(32'b0),
      .iBusWishbone_CYC(iCYC), .iBusWishbone_STB(iSTB), .iBusWishbone_ACK(iACK),
      .iBusWishbone_WE(iWE), .iBusWishbone_ADR(iADR),
      .iBusWishbone_DAT_MISO(iMISO), .iBusWishbone_DAT_MOSI(iMOSI),
      .iBusWishbone_SEL(iSEL), .iBusWishbone_ERR(1'b0),
      .dBusWishbone_CYC(dCYC), .dBusWishbone_STB(dSTB), .dBusWishbone_ACK(dACK),
      .dBusWishbone_WE(dWE), .dBusWishbone_ADR(dADR),
      .dBusWishbone_DAT_MISO(dMISO), .dBusWishbone_DAT_MOSI(dMOSI),
      .dBusWishbone_SEL(dSEL), .dBusWishbone_ERR(1'b0),
      .clk(clk), .reset(reset), .debugReset(1'b0));

   // ---- memory -------------------------------------------------------------
   reg [31:0] flash [0:FLASH_WORDS-1];
   reg [31:0] ram   [0:RAM_WORDS-1];
   integer i;
   initial begin
      for (i = 0; i < FLASH_WORDS; i = i + 1) flash[i] = 32'h00000013; // nop
      for (i = 0; i < RAM_WORDS;   i = i + 1) ram[i]   = 32'h0;
      $readmemh("fw.hex", flash);
   end

   // byte address = {ADR, 2'b00}
   function [31:0] rd(input [29:0] a);
      reg [31:0] byteaddr;
      begin
         byteaddr = {a, 2'b00};
         if (byteaddr >= FLASH_BASE) rd = flash[(byteaddr - FLASH_BASE) >> 2];
         else                        rd = ram[byteaddr[10:2]];
      end
   endfunction

   integer ilat = 0, dlat = 0;
   always @(posedge clk) begin
      // instruction bus
      if (iCYC && iSTB && !iACK) begin
         if (ilat >= MEM_LAT) begin iMISO <= rd(iADR); iACK <= 1; ilat <= 0; end
         else ilat <= ilat + 1;
      end else begin iACK <= 0; if (!iCYC) ilat <= 0; end
      // data bus
      if (dCYC && dSTB && !dACK) begin
         if (dlat >= MEM_LAT) begin
            if (dWE) begin
               if ({dADR, 2'b00} < FLASH_BASE) begin
                  if (dSEL[0]) ram[dADR[8:0]][ 7: 0] <= dMOSI[ 7: 0];
                  if (dSEL[1]) ram[dADR[8:0]][15: 8] <= dMOSI[15: 8];
                  if (dSEL[2]) ram[dADR[8:0]][23:16] <= dMOSI[23:16];
                  if (dSEL[3]) ram[dADR[8:0]][31:24] <= dMOSI[31:24];
               end
            end else dMISO <= rd(dADR);
            dACK <= 1; dlat <= 0;
         end else dlat <= dlat + 1;
      end else begin dACK <= 0; if (!dCYC) dlat <= 0; end
   end

   // ---- guarantee monitors -------------------------------------------------
   integer viol = 0;
   integer cycles = 0;
   integer i_txn = 0, d_txn = 0, d_wr = 0;
   reg [29:0] i_adr_h, d_adr_h;  reg d_we_h;  reg [3:0] d_sel_h;
   reg i_busy = 0, d_busy = 0;
   integer i_age = 0, d_age = 0;

   task viol_msg(input [511:0] m);
      begin $display("VIOLATION: %0s at cycle %0d", m, cycles); viol = viol + 1; end
   endtask

   always @(posedge clk) if (!reset) begin
      cycles = cycles + 1;

      // G1: STB implies CYC
      if (iSTB && !iCYC) viol_msg("iBus STB without CYC");
      if (dSTB && !dCYC) viol_msg("dBus STB without CYC");
      // G4: the instruction bus never writes
      if (iWE) viol_msg("iBus asserted WE");

      // G2: request attributes stable until ACK; G3: bounded termination
      if (iCYC && iSTB) begin
         if (!i_busy) begin i_busy <= 1; i_adr_h <= iADR; i_age <= 0; end
         else begin
            if (iADR !== i_adr_h) viol_msg("iBus ADR changed mid-transaction");
            i_age <= i_age + 1;
            if (i_age > 64) viol_msg("iBus transaction exceeded 64 cycles");
         end
         if (iACK) begin i_busy <= 0; i_txn = i_txn + 1; end
      end else i_busy <= 0;

      if (dCYC && dSTB) begin
         if (!d_busy) begin
            d_busy <= 1; d_adr_h <= dADR; d_we_h <= dWE; d_sel_h <= dSEL; d_age <= 0;
         end else begin
            if (dADR !== d_adr_h) viol_msg("dBus ADR changed mid-transaction");
            if (dWE  !== d_we_h)  viol_msg("dBus WE changed mid-transaction");
            if (dSEL !== d_sel_h) viol_msg("dBus SEL changed mid-transaction");
            d_age <= d_age + 1;
            if (d_age > 64) viol_msg("dBus transaction exceeded 64 cycles");
         end
         if (dACK) begin
            d_busy <= 0; d_txn = d_txn + 1; if (dWE) d_wr = d_wr + 1;
         end
      end else d_busy <= 0;
   end

   // ---- retirement gaps (L5/01's measure `m`) ------------------------------
   // `m` bounds cycles-to-next-retirement. The commit point is the writeBack
   // stage (L5/00), and `writeBack_arbitration_isFiring` pulses exactly when an
   // instruction leaves it — every instruction, not just register writers, so
   // stores and jumps are counted too. We
   // record the OBSERVED gap distribution — a lower bound on the true worst case
   // (this is one execution), which is exactly what a measured bound can claim.
   integer retired = 0, gap = 0, gap_max = 0, gap_sum = 0;
   integer gap_hist [0:63];
   integer gi;
   initial for (gi = 0; gi < 64; gi = gi + 1) gap_hist[gi] = 0;

   always @(posedge clk) if (!reset) begin
      if (core.writeBack_arbitration_isFiring) begin
         retired = retired + 1;
         if (retired > 1) begin
            gap_sum = gap_sum + gap;
            if (gap > gap_max) gap_max = gap;
            gap_hist[(gap > 63) ? 63 : gap] = gap_hist[(gap > 63) ? 63 : gap] + 1;
         end
         gap = 0;
      end else if (retired > 0) gap = gap + 1;
   end

   // ---- run ----------------------------------------------------------------
   initial begin
      repeat (8) @(posedge clk);
      reset = 0;
      while (cycles < MAX_CYCLES) @(posedge clk);
      $display("SUMMARY cycles=%0d ibus_txn=%0d dbus_txn=%0d dbus_writes=%0d violations=%0d",
               cycles, i_txn, d_txn, d_wr, viol);
      $display("RETIRE retired=%0d gap_max=%0d", retired, gap_max);
      for (gi = 0; gi < 64; gi = gi + 1)
         if (gap_hist[gi] != 0) $display("GAP %0d %0d", gi, gap_hist[gi]);
      $finish;
   end
endmodule
