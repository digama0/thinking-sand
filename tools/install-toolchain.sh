#!/usr/bin/env bash
# install-toolchain.sh — install the EDA/build tools the checker phase is blocked on.
#
# Everything here is PINNED to an exact version and verified against a recorded
# sha256, for the same reason tools/fetch-data.sh pins commit SHAs: findings.md
# quotes numbers produced by these tools, and a floating toolchain would silently
# invalidate them. If you deliberately move to a newer tool, bump the version AND
# its hash here, re-run, and re-derive the affected findings.
#
# Most of it needs NO root: four upstream prebuilt tarballs unpacked into a prefix.
# Only OpenSTA is built from source, and only that needs apt (its own upstream
# Dockerfile.ubuntu24.04 is mirrored exactly — same package list, same CUDD).
#
#   tools/install-toolchain.sh                 # everything (asks before sudo)
#   tools/install-toolchain.sh --no-root       # skip OpenSTA, no sudo at all
#   tools/install-toolchain.sh --only sta      # one group; repeatable
#   tools/install-toolchain.sh --list          # what would be installed, and why
#   tools/install-toolchain.sh --prefix DIR    # default ~/.local/thinking-sand
#
# Groups: cad (yosys/verilator/iverilog/sby/SMT), riscv (gcc), sta (OpenSTA),
#         sbt (SpinalHDL builds), mdbook (the book).
#
# Afterwards: source <prefix>/env.sh   (or add <prefix>/bin to PATH)
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$PWD

PREFIX="${HOME}/.local/thinking-sand"
NO_ROOT=0; LIST_ONLY=0; SELECTED=()

# ---- pinned versions ---------------------------------------------------------
# oss-cad-suite bundles yosys, verilator, iverilog, SymbiYosys and the SMT solvers
# (z3, bitwuzla, yices, boolector) in one self-contained tree — 737 MB download.
CAD_TAG=2026-08-02
CAD_FILE=oss-cad-suite-linux-x64-20260802.tgz
CAD_URL=https://github.com/YosysHQ/oss-cad-suite-build/releases/download/$CAD_TAG/$CAD_FILE
CAD_SHA=cb3d2899eb7860241cb7b21567428601c7ee864e30838c14b23ea91749c89d00

RISCV_VER=15.2.0-1
RISCV_FILE=xpack-riscv-none-elf-gcc-$RISCV_VER-linux-x64.tar.gz
RISCV_URL=https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/releases/download/v$RISCV_VER/$RISCV_FILE
RISCV_SHA=aaaa8060c914851a3e5ee1ba82cc3d6f80972f90638a05c6e823a37557a33758

MDBOOK_VER=v0.5.4
MDBOOK_FILE=mdbook-$MDBOOK_VER-x86_64-unknown-linux-gnu.tar.gz
MDBOOK_URL=https://github.com/rust-lang/mdBook/releases/download/$MDBOOK_VER/$MDBOOK_FILE
MDBOOK_SHA=3f28de05dafca9d0f2eab99c662116b0e37b89b1d96a08f8f430b9eeae958cd7

# sbt 1.x deliberately: VexRiscv/SpinalHDL build definitions are sbt 1 projects.
# (The launcher still honours project/build.properties, so it fetches whatever
# exact sbt that repo pins.)
SBT_VER=1.12.14
SBT_FILE=sbt-$SBT_VER.tgz
SBT_URL=https://github.com/sbt/sbt/releases/download/v$SBT_VER/$SBT_FILE
SBT_SHA=cd17daae220ff264faa4251334522444518584f0eb2ee82da01523a9b9002b7e

# OpenSTA + CUDD, both exactly as upstream's Dockerfile.ubuntu24.04 does it
STA_SHA1=3f4b337e30afccf8075118860daf2e4fea8a5c18          # 2026-07-31
CUDD_URL=https://raw.githubusercontent.com/davidkebo/cudd/main/cudd_versions/cudd-3.0.0.tar.gz
CUDD_SHA=b8e966b4562c96a03e7fbea239729587d7b395d53cadcc39a7203b49cf7eeb69
STA_APT="git wget cmake gcc g++ tcl-dev tcl-tclreadline swig bison flex automake autotools-dev libeigen3-dev libfmt-dev zlib1g-dev"

while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) PREFIX="$2"; shift 2 ;;
    --no-root) NO_ROOT=1; shift ;;
    --only) SELECTED+=("$2"); shift 2 ;;
    --list) LIST_ONLY=1; shift ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
  esac
done
[ ${#SELECTED[@]} -gt 0 ] || SELECTED=(cad riscv sta sbt mdbook)
want() { for g in "${SELECTED[@]}"; do [ "$g" = "$1" ] && return 0; done; return 1; }

OPT="$PREFIX/opt"; BIN="$PREFIX/bin"; DL="$PREFIX/download"

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
skip() { printf '   already installed: %s\n' "$*"; }

# ---- what each group unblocks (kept in sync with the layer scoreboards) ------
if [ "$LIST_ONLY" = 1 ]; then
  cat <<'EOF'
group   tools                                    unblocks (tools/check-l*.py rows)
------  ---------------------------------------  --------------------------------------------
cad     yosys, verilator, iverilog, sby,         L3/rho-reproduction (re-run synthesis from the
        z3/bitwuzla/yices/boolector              pinned OpenLane config and diff the netlist)
                                                 L4/differential (elaborate vs Verilator+Icarus)
                                                 L4/latch-complete, L4/rtl-scc (yosys as the
                                                   untrusted Verilog front end)
                                                 L5/rvfi-alpha, L5/bus-guarantee (simulate, then
                                                   check alpha and the Wishbone clauses on traces)
                                                 L5/ic3-calibrate (SymbiYosys drives the IC3/PDR
                                                   engine the invariant work needs sizing against)
riscv   riscv-none-elf-{gcc,objdump,...}         builds a concrete flash image F, which is what
                                                   the UB-free-image and flash-immutability
                                                   (L7/f-immutable) properties are checked ON;
                                                   extends L5/irq-anchors past static reading
sta     OpenSTA (+ CUDD)                         L2/f1-match — THE blocker on F1: re-run STA from
                                                   the pinned netlist/SDC/Liberty and reproduce
                                                   the three failing hold corners per-path
                                                 L2/verified-sta, L7/oc-rows
sbt     sbt (SpinalHDL/VexRiscv builds)          L4/04 obligation 3 — regenerate the CORE half of
                                                   the RTL, the half tools/replicate.py cannot
                                                   reach today (the SoC half is already covered)
mdbook  mdbook                                   tools/build-book.sh renders the book locally
EOF
  exit 0
fi

mkdir -p "$OPT" "$BIN" "$DL"

get() {  # get <url> <sha256> <dest-filename>
  local url="$1" sha="$2" out="$DL/$3"
  if [ -s "$out" ] && [ "$(sha256sum "$out" | cut -d' ' -f1)" = "$sha" ]; then
    printf '   cached  %s\n' "$3"; return
  fi
  printf '   fetch   %s\n' "$3"
  curl -fL --progress-bar -o "$out" "$url"
  local got; got=$(sha256sum "$out" | cut -d' ' -f1)
  if [ "$got" != "$sha" ]; then
    echo "   !! sha256 MISMATCH for $3" >&2
    echo "      expected $sha" >&2
    echo "      got      $got" >&2
    rm -f "$out"; exit 1
  fi
}

link() { ln -sfn "$1" "$BIN/$(basename "${2:-$1}")"; }

# ---- cad: yosys / verilator / iverilog / sby / SMT solvers -------------------
if want cad; then
  say "OSS CAD Suite ($CAD_TAG) — yosys, verilator, iverilog, SymbiYosys, SMT solvers"
  if [ -x "$OPT/oss-cad-suite/bin/yosys" ]; then skip "$OPT/oss-cad-suite"; else
    get "$CAD_URL" "$CAD_SHA" "$CAD_FILE"
    echo "   unpack  (~737 MB, takes a minute)"
    tar -xzf "$DL/$CAD_FILE" -C "$OPT"
  fi
  # The suite ships its own libs; its binaries must run through its environment,
  # so wrap rather than symlink — a bare symlink picks up the host's libstdc++.
  for t in yosys verilator iverilog vvp sby z3 bitwuzla yices-smt2; do
    [ -x "$OPT/oss-cad-suite/bin/$t" ] || continue
    cat > "$BIN/$t" <<EOF
#!/usr/bin/env bash
source "$OPT/oss-cad-suite/environment"
exec "$OPT/oss-cad-suite/bin/$t" "\$@"
EOF
    chmod +x "$BIN/$t"
  done
fi

# ---- riscv: bare-metal cross compiler ---------------------------------------
if want riscv; then
  say "riscv-none-elf-gcc ($RISCV_VER) — bare-metal RV32 cross toolchain"
  RVDIR="$OPT/xpack-riscv-none-elf-gcc-$RISCV_VER"
  if [ -x "$RVDIR/bin/riscv-none-elf-gcc" ]; then skip "$RVDIR"; else
    get "$RISCV_URL" "$RISCV_SHA" "$RISCV_FILE"
    echo "   unpack"
    tar -xzf "$DL/$RISCV_FILE" -C "$OPT"
  fi
  for f in "$RVDIR"/bin/riscv-none-elf-*; do link "$f"; done
fi

# ---- mdbook -----------------------------------------------------------------
if want mdbook; then
  say "mdbook ($MDBOOK_VER) — renders the book"
  if [ -x "$OPT/mdbook/mdbook" ]; then skip "$OPT/mdbook/mdbook"; else
    get "$MDBOOK_URL" "$MDBOOK_SHA" "$MDBOOK_FILE"
    mkdir -p "$OPT/mdbook"; tar -xzf "$DL/$MDBOOK_FILE" -C "$OPT/mdbook"
  fi
  link "$OPT/mdbook/mdbook"
fi

# ---- sbt --------------------------------------------------------------------
if want sbt; then
  say "sbt ($SBT_VER) — for SpinalHDL/VexRiscv regeneration"
  if ! command -v java >/dev/null 2>&1; then
    echo "   !! java not found; sbt needs a JDK (apt install default-jdk)" >&2
  fi
  if [ -x "$OPT/sbt/bin/sbt" ]; then skip "$OPT/sbt"; else
    get "$SBT_URL" "$SBT_SHA" "$SBT_FILE"
    tar -xzf "$DL/$SBT_FILE" -C "$OPT"
  fi
  link "$OPT/sbt/bin/sbt"
fi

# ---- sta: OpenSTA, built from source ----------------------------------------
if want sta; then
  say "OpenSTA (${STA_SHA1:0:10}) + CUDD 3.0.0 — the F1 blocker"
  if [ -x "$OPT/OpenSTA/build/sta" ]; then skip "$OPT/OpenSTA/build/sta"; link "$OPT/OpenSTA/build/sta"
  elif [ "$NO_ROOT" = 1 ]; then
    echo "   skipped (--no-root): OpenSTA needs apt for tcl-dev/swig/bison/flex/eigen/fmt"
  else
    echo "   OpenSTA is the one source build. Its upstream Dockerfile.ubuntu24.04"
    echo "   installs these system packages, and this mirrors it exactly:"
    echo "     $STA_APT"
    read -r -p "   run 'sudo apt-get install' for them now? [y/N] " ans
    if [ "${ans:-N}" != "y" ] && [ "${ans:-N}" != "Y" ]; then
      echo "   skipped. Re-run with --only sta once the packages are present."
    else
      sudo apt-get update
      sudo apt-get install -y $STA_APT
      get "$CUDD_URL" "$CUDD_SHA" cudd-3.0.0.tar.gz
      if [ ! -f "$OPT/cudd-3.0.0/cudd/.libs/libcudd.a" ] && [ ! -f "$OPT/cudd-3.0.0/cudd/libcudd.a" ]; then
        echo "   build   CUDD"
        tar -xzf "$DL/cudd-3.0.0.tar.gz" -C "$OPT"
        ( cd "$OPT/cudd-3.0.0" && ./configure >/dev/null && make -j"$(nproc)" >/dev/null )
      fi
      [ -d "$OPT/OpenSTA/.git" ] || git clone https://github.com/parallaxsw/OpenSTA.git "$OPT/OpenSTA"
      ( cd "$OPT/OpenSTA" && git fetch --all -q && git checkout -q "$STA_SHA1" \
        && rm -rf build && mkdir build && cd build \
        && cmake -DCUDD_DIR="$OPT/cudd-3.0.0" .. >/dev/null \
        && make -j"$(nproc)" )
      link "$OPT/OpenSTA/build/sta"
    fi
  fi
fi

# ---- environment ------------------------------------------------------------
cat > "$PREFIX/env.sh" <<EOF
# source this (or add \$PREFIX/bin to PATH) to use the pinned toolchain
export PATH="$BIN:\$PATH"
EOF
cat > "$PREFIX/env.fish" <<EOF
# source this from fish
fish_add_path "$BIN"
EOF

say "installed under $PREFIX"
printf '   bash/zsh:  source %s/env.sh\n' "$PREFIX"
printf '   fish:      source %s/env.fish\n\n' "$PREFIX"
for t in yosys verilator iverilog sby riscv-none-elf-gcc sta sbt mdbook; do
  if [ -x "$BIN/$t" ]; then printf '   \033[32m%-22s\033[0m %s\n' "$t" "ok"
  else printf '   %-22s %s\n' "$t" "not installed"; fi
done
cat <<'EOF'

Next: `tools/install-toolchain.sh --list` maps each tool to the scoreboard rows it
unblocks. The rows stay TODO until a checker actually uses the tool — installing it
is the precondition, not the work.
EOF
