package chipyard

import org.chipsalliance.cde.config.{Config}

// TinyRocketConfig + spike co-simulation: the trace port drives SpikeCosim,
// which steps the golden model per committed instruction and compares.
// WithDebugROB gives the trace port writeback data (traceHasWdata), which
// the comparison needs. (thinking-sand: the L5 trace-oracle configuration.)
class CospikeTinyRocketConfig extends Config(
  new chipyard.harness.WithCospike ++
  new chipyard.config.WithTraceIO ++
  new freechips.rocketchip.rocket.WithDebugROB ++
  new TinyRocketConfig)
