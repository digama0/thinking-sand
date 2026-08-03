#!/usr/bin/env python3
"""config-record.py — extract the shipped configuration record from the pinned
RTL pair (L4/00's `Config`, L5/00 obligation 1).

Everything below is *measured* from `VexRiscv_MinDebugCache.v` (SpinalHDL
output) and `mgmt_core.v` (LiteX output); nothing is quoted from
documentation. The record is what decides which ISA subset L6 must cover,
what the invariant must describe, and which register-dependent hypotheses
(reset vector!) become reachability conditions.

Usage: config-record.py            (prints the record)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _core_v(root):
    """The TARGET core: the regenerated one when present, else the shipped 2021
    artifact. See tools/checklib.py:core_v — one source of truth, two readers."""
    t = root / "data/mgmt/VexRiscv_target.v"
    return t if t.is_file() else root / "data/mgmt/VexRiscv_MinDebugCache.v"

VEX = _core_v(ROOT)
LITEX = ROOT / "data/mgmt/mgmt_core.v"

# machine-mode CSR names for the addresses we may find
CSR_NAMES = {0x300: "mstatus", 0x301: "misa", 0x304: "mie", 0x305: "mtvec",
             0x340: "mscratch", 0x341: "mepc", 0x342: "mcause", 0x343: "mtval",
             0x344: "mip", 0xC00: "cycle", 0xC02: "instret",
             0xBC0: "custom-0xBC0 (LiteX external-IRQ mask)",
             0xFC0: "custom-0xFC0 (LiteX external-IRQ pending)"}


def record():
    vex = VEX.read_text(errors="replace")
    lit = LITEX.read_text(errors="replace")
    r = {}

    # ISA: no compressed decode, no mul/div state, no atomics
    r["compressed"] = bool(re.search(r"[Cc]ompress", vex))
    r["muldiv"] = "MulDivIterativePlugin" in vex
    r["atomics"] = bool(re.search(r"\bAMO|LRSC|lrsc", vex))
    r["wfi"] = "32'h10500073" in vex

    # CSR address set. Take ONLY addresses that are decoded into a per-register
    # select — `execute_CsrPlugin_csr_N <= (decode_INSTRUCTION[31:20] == 12'hXXX)`.
    # Grepping every 12-bit literal instead (the first version of this) also
    # picks up the counter-permission MASKS (`csrAddress & 12'hf60 == 12'hb00`)
    # and the PMP range checks, reporting them as implemented registers. That
    # happened to be harmless on the 2021 core, which has no counter logic, and
    # wrong the moment a newer generator adds some.
    r["csrs"] = sorted({int(h, 16) for h in re.findall(
        r"execute_CsrPlugin_csr_\d+ <= \(decode_INSTRUCTION\[31 : 20\] == 12'h([0-9a-f]+)\)",
        vex)})

    # I-cache geometry from the memory array declarations
    m = re.search(r"reg \[(\d+):0\] banks_0 \[0:(\d+)\]", vex)
    t = re.search(r"reg \[(\d+):0\] ways_0_tags \[0:(\d+)\]", vex)
    words, lines = int(m.group(2)) + 1, int(t.group(2)) + 1
    r["icache"] = {"bytes": 4 * words, "lines": lines,
                   "line_bytes": 4 * words // lines, "tag_bits": int(t.group(1)) + 1,
                   "ways": 1 + len(re.findall(r"ways_1_tags", vex))}

    # hazard style: does a writeBackBuffer address match STALL (interlock) or forward?
    stall = re.search(r"if\(HazardSimplePlugin_addr0Match\) begin\s*\n\s*"
                      r"HazardSimplePlugin_src0Hazard = 1'b1;", vex)
    r["hazards"] = "interlock (match => stall)" if stall else "UNRECOGNISED - inspect"

    # LiteX side: reset vector register, interrupt wiring
    rv = re.search(r"reg \[31:0\] mgmtsoc_vexriscv = 32'd(\d+);", lit)
    r["reset_vector"] = {"register": "mgmtsoc_vexriscv (CSR-writable)",
                         "init": hex(int(rv.group(1))) if rv else "NOT FOUND"}
    r["sw_timer_irq_tied_0"] = bool(
        re.search(r"\.softwareInterrupt\(1'd0\)", lit)
        and re.search(r"\.timerInterrupt\(1'd0\)", lit))
    ia = re.search(r"reg \[(\d+):0\] mgmtsoc_interrupt", lit)
    r["ext_irq_array_bits"] = int(ia.group(1)) + 1 if ia else None
    r["buses"] = {"iBus": "Wishbone (+CTI/BTE burst)" if ".iBusWishbone_CTI" in lit else "?",
                  "dBus": "Wishbone (+CTI/BTE burst)" if ".dBusWishbone_CTI" in lit else "?"}
    return r


def choices():
    """The measurable choice-register rows (L6/02) and trap-detail deviations,
    read from the shipped core. Each value is a *presence check* of the exact
    generated construct, so a re-generation that changes behaviour flips it."""
    vex = VEX.read_text(errors="replace")
    c = {}

    # C2 — misaligned data accesses: trap (word: addr[1:0]!=0, half: addr[0]!=0),
    # with the bus command SUPPRESSED (no side effect), causes 4 (load) / 6 (store)
    c["C2_misaligned"] = {
        "detect": bool(re.search(
            r"assign execute_ALIGNEMENT_FAULT = \(\(\(dBus_cmd_payload_size == 2'b10\) "
            r"&& \(dBus_cmd_payload_address\[1 : 0\] != 2'b00\)\) \|\| "
            r"\(\(dBus_cmd_payload_size == 2'b01\) && "
            r"\(dBus_cmd_payload_address\[0 : 0\] != 1'b0\)\)\);", vex)),
        "bus_cmd_suppressed": bool(re.search(
            r"if\(execute_ALIGNEMENT_FAULT\) begin\s*\n\s*"
            r"execute_DBusSimplePlugin_skipCmd = 1'b1;", vex)),
        "causes_4_load_6_store": "(memory_MEMORY_STORE ? 3'b110 : 3'b100)" in vex,
    }

    # C3/C6 — illegal instruction: cause 2, mtval = the instruction word
    c["C3_illegal"] = {
        "cause_2": "assign decodeExceptionPort_payload_code = 4'b0010;" in vex,
        "mtval_instruction":
            "assign decodeExceptionPort_payload_badAddr = decode_INSTRUCTION;" in vex,
    }

    # C5 — mtvec: base[31:2] and mode[1:0] both writable and STORED, but the
    # trap redirect is unconditionally {base,00} — vectored mode is not
    # implemented, the mode bits are inert storage; and mtvec has NO reset value
    c["C5_mtvec"] = {
        "base_writable": bool(re.search(
            r"CsrPlugin_mtvec_base <= CsrPlugin_csrMapping_writeDataSignal\[31 : 2\];", vex)),
        # mtvec is WRITE-ONLY in both cores: its legality is gated on
        # CSR_WRITE_OPCODE, so a pure read (csrr mtvec) is an illegal access
        # and traps. The mode field is therefore unobservable either way —
        # 2021 stored it, the 2026 generator drops the write entirely.
        "write_only": bool(re.search(
            r"if\(execute_CsrPlugin_csr_773\) begin\s*\n\s*"
            r"if\(execute_CSR_WRITE_OPCODE\) begin\s*\n\s*"
            r"execute_CsrPlugin_illegalAccess = 1'b0;", vex)),
        "redirect_ignores_mode":
            "CsrPlugin_jumpInterface_payload = {CsrPlugin_xtvec_base,2'b00};" in vex
            and not re.search(r"xtvec_mode\s*==", vex),
        "no_reset_value": not re.search(r"CsrPlugin_mtvec_(base|mode) <= (?!CsrPlugin_csrMapping)", vex),
    }

    # C6 — the remaining mtval sources: one context register feeds mtval on
    # every trap; per-cause payloads measured at their ports
    c["C6_mtval_sources"] = {
        "single_write_site":
            len(re.findall(r"CsrPlugin_mtval <= ", vex)) == 1,
        "fetch_fault_addr_aligned": bool(re.search(
            r"assign IBusCachedPlugin_decodeExceptionPort_payload_badAddr = "
            r"\{IBusCachedPlugin_iBusRsp_stages_2_input_payload\[31 : 2\],2'b00\};", vex)),
        "load_store_addr":
            "assign DBusSimplePlugin_memoryExceptionPort_payload_badAddr = memory_REGFILE_WRITE_DATA;" in vex,
        "branch_target":
            "assign BranchPlugin_branchExceptionPort_payload_badAddr = BranchPlugin_jumpInterface_payload;" in vex,
        "ecall_writes_instruction":
            "assign CsrPlugin_selfException_payload_badAddr = execute_INSTRUCTION;" in vex,
    }

    # deviations from the ratified trap semantics, measured
    c["ebreak_no_exception"] = {
        # EBREAK only feeds the debug-halt path, gated on an active debug session;
        # there is no breakpoint (cause 3) exception path at all
        "debug_gated": bool(re.search(
            r"assign decode_DO_EBREAK = \(\(\(! DebugPlugin_haltIt\) && "
            r"\(decode_IS_EBREAK \|\| 1'b0\)\) && DebugPlugin_allowEBreak\);", vex)),
        "no_cause_3_path": "= 4'b0011;" not in
            "".join(re.findall(r"ExceptionPort_payload_code = .*;|selfException_payload_code = .*;", vex)),
    }
    c["ecall_cause_11"] = bool(re.search(
        r"default : begin\s*\n\s*CsrPlugin_selfException_payload_code = 4'b1011;", vex))
    # access faults are UNREACHABLE: the core's own Wishbone bridges tie both
    # error inputs to zero (the SoC-side ERR wiring is discarded at the core
    # boundary), and the MMU exception path is tied off — so the cause-1/5/7
    # logic that exists in the plugins is structurally dead. Additionally the
    # load-only guard means even a live dBus error would never fault a store.
    c["access_faults_unreachable"] = {
        "ibus_err_tied_0": "assign iBus_rsp_payload_error = 1'b0;" in vex,
        "dbus_err_tied_0": "assign dBus_rsp_error = 1'b0;" in vex,
        "mmu_path_tied_off": "assign IBusCachedPlugin_mmuBus_rsp_isPaging = 1'b0;" in vex,
        # the label is generator line-numbering, so match the predicate only
        "store_error_ignored_anyway": bool(re.search(
            r"assign when_DBusSimplePlugin_l\d+ = \(\(dBus_rsp_ready && dBus_rsp_error\) "
            r"&& \(! memory_MEMORY_STORE\)\);", vex)),
    }
    c["branch_misaligned_cause_0"] = \
        "assign BranchPlugin_branchExceptionPort_payload_code = 4'b0000;" in vex
    # the complete reachable synchronous trap surface follows: causes
    # 0 (fetch-target misaligned), 2 (illegal), 4/6 (load/store misaligned),
    # 11 (ecall); interrupts: external (11) only, software/timer tied off
    return c


def main():
    r = record()
    print("# The shipped configuration record (measured)\n")
    print(f"ISA            : RV32I — compressed={r['compressed']}, "
          f"hardware mul/div={r['muldiv']}, atomics={r['atomics']}, wfi={r['wfi']}")
    print("CSRs           : " + ", ".join(
        f"0x{a:03X} ({CSR_NAMES.get(a, 'UNKNOWN')})" for a in r["csrs"]))
    absent = [f"0x{a:03X} ({n})" for a, n in CSR_NAMES.items()
              if a not in r["csrs"] and a not in (0xBC0, 0xFC0)]
    print("  notably absent: " + ", ".join(absent))
    ic = r["icache"]
    print(f"I-cache        : {ic['bytes']} B total — {ic['lines']} lines x "
          f"{ic['line_bytes']} B, {ic['ways']} way (direct-mapped), tag {ic['tag_bits']} bits")
    print(f"hazards        : {r['hazards']}")
    print(f"reset vector   : {r['reset_vector']['register']} = {r['reset_vector']['init']}")
    print(f"interrupts     : software/timer tied to 0 = {r['sw_timer_irq_tied_0']}; "
          f"external array width {r['ext_irq_array_bits']}")
    print(f"buses          : iBus {r['buses']['iBus']}; dBus {r['buses']['dBus']}")

    print("\n# The measured choice-register rows (L6/02) and trap details\n")
    for row, val in choices().items():
        if isinstance(val, dict):
            bad = [k for k, v in val.items() if not v]
            print(f"{row:<34}: {'all measured facts hold' if not bad else 'CHANGED: ' + ', '.join(bad)}")
        else:
            print(f"{row:<34}: {val}")


if __name__ == "__main__":
    main()
