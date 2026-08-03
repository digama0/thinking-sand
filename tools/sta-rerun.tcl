# sta-rerun.tcl — re-run the shipped signoff timing analysis from pinned inputs.
#
# This is the F1 obligation (L2/04, findings "F1 confronted"): the shipped
# signoff.rpt records three SLOW corners failing hold, but the per-path evidence
# for the failing corners was never committed. The reports that ARE committed
# (42-rcx_sta.{min,max}.rpt) are the NOMINAL corner. So the failing paths have
# never been visible — until this script reproduces them.
#
# Inputs are exactly what openlane/caravel_core/config.tcl's EXTRA_LIBS names,
# plus the sky130 Liberty from the pinned open_pdks build (12df12e2, fetched by
# volare) and the RCX-extracted SPEF the shipped run used. Nothing improvised.
#
#   sta -no_init -exit tools/sta-rerun.tcl
#
# Environment (all optional, defaults shown):
#   STA_CORNER=ss_100C_1v60     which sky130 Liberty corner ("s" = slow = failing)
#   STA_PDK=/tmp/pdk            volare --pdk-root
#   STA_SPEF=...nom.spef        which RC corner
set corner [expr {[info exists env(STA_CORNER)] ? $env(STA_CORNER) : "ss_100C_1v60"}]
set pdk    [expr {[info exists env(STA_PDK)]    ? $env(STA_PDK)    : "/tmp/pdk"}]
set root   [file normalize [file dirname [info script]]/..]
set spef   [expr {[info exists env(STA_SPEF)] ? $env(STA_SPEF) : \
                  "$root/data/caravel/spef/caravel_core.nom.spef"}]

puts "== corner  : $corner"
puts "== spef    : [file tail $spef]"

# --- Liberty: the standard cells, then every macro EXTRA_LIBS listed ----------
read_liberty $pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__$corner.lib
foreach l {housekeeping gpio_defaults_block gpio_logic_high mprj_io_buffer
           user_project_wrapper caravel_clocking RAM128.nom} {
  read_liberty $root/data/caravel/lib/$l.lib
}

# --- the shipped gate netlist ------------------------------------------------
read_verilog $root/data/caravel/gl_caravel_core.sta.v
link_design caravel_core

# --- parasitics + the caravel_core run's OWN sdc (not the chip-level one) -----
read_spef $spef
read_sdc $root/data/caravel/caravel_core.sdc

puts "\n===== HOLD (min) ============================================="
report_checks -path_delay min -group_count 5 -slack_max 0 -format full_clock_expanded
puts "\n===== SETUP (max) ============================================"
report_checks -path_delay max -group_count 5 -slack_max 0 -format full_clock_expanded
puts "\n===== WORST SLACK ============================================"
report_worst_slack -min
report_worst_slack -max
puts "\n===== TOTAL NEGATIVE SLACK ==================================="
report_tns
report_wns
