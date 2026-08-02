# sdc-elaborate.tcl — flatten an SDC (Tcl) file into a per-mode constraint inventory.
#
# The SDC is a program: variables, conditionals, mode branches. Nothing can be
# classified until it is elaborated into flat constraint sets (L2/04 step zero).
# This harness stubs every SDC command to log its fully-resolved argument list,
# forces the three mode variables, and evaluates the file.
#
# Usage:  tclsh sdc-elaborate.tcl <file.sdc> <io_4_mode> <ios_mode> <io_sync>
#         io_4_mode in {SCK, GPIO};  ios_mode in {IN, OUT};  io_sync in {0, 1}
# Output: one line per constraint command:  <line>\t<command>\t<resolved args>
#         Object queries [get_ports ...] etc. resolve to their literal query text.

if {$argc != 4} {
    puts stderr "usage: tclsh sdc-elaborate.tcl <file.sdc> <SCK|GPIO> <IN|OUT> <0|1>"
    exit 2
}
lassign $argv sdcfile io4 ios sync

# --- stubs ------------------------------------------------------------------
# Object queries: return the query as literal text (brackets are not re-evaluated
# in a command-substitution result, so this is safe and keeps the log readable).
foreach q {get_ports get_pins get_clocks get_nets get_cells all_inputs all_outputs all_clocks current_design} {
    proc $q {args} "return \"\\\[$q \$args\\\]\""
}

# Constraint commands: log with the source line for provenance.
proc log_cmd {cmd args} {
    set line ?
    catch { set line [dict get [info frame -2] line] }
    real_puts "$line\t$cmd\t[join $args { }]"
}
foreach c {create_clock set_clock_uncertainty set_propagated_clock set_clock_groups
           set_false_path set_case_analysis set_multicycle_path set_min_delay set_max_delay
           set_input_delay set_output_delay set_input_transition set_load
           set_max_fanout set_max_transition set_max_capacitance set_timing_derate
           set_driving_cell set_units} {
    proc $c {args} "log_cmd $c {*}\$args"
}
# Anything not stubbed resolves to its literal text and is reported on stderr,
# so a constraint command missing from the stub list cannot vanish silently.
# (The shipped caravel.sdc needs this for a benign reason: a puts string contains
# an unescaped command substitution `IO[4]`.)
proc unknown {cmd args} {
    # Bare numerics and * are bus indices from unbraced port names (mprj_io[4]):
    # reconstruct them silently and exactly. Anything else is reported.
    if {[llength $args] == 0 && [regexp {^(\d+|\*)$} $cmd]} {
        return "\[$cmd\]"
    }
    real_puts stderr "UNKNOWN-COMMAND\t$cmd\t[join $args { }]"
    return "\[$cmd $args\]"
}

rename puts real_puts
proc puts {args} {
    # Swallow the SDC's own [INFO] chatter; keep the harness's own output working.
    if {[lindex $args 0] eq "stderr" || [lindex $args 0] eq "stdout"} {
        real_puts {*}$args
    }
}
proc harness_out {s} { real_puts $s }

# --- force the mode variables ----------------------------------------------
set f [open $sdcfile r]; set script [read $f]; close $f
regsub -line {^set io_4_mode .*$}      $script "set io_4_mode $io4"      script
regsub -line {^set ios_mode .*$}       $script "set ios_mode $ios"       script
regsub -line {^set ::env\(IO_SYNC\) .*$} $script "set ::env(IO_SYNC) $sync" script

harness_out "#mode\tio_4_mode=$io4 ios_mode=$ios IO_SYNC=$sync"
eval $script
