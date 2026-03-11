# Sentinel Metrics

## Core metrics

- **gateway_failures_per_day**
- **heal_attempts_per_day** (by method)
- **successful_heals_per_day**
- **latency_spikes_per_day** (after debouncing)
- **cost_today** vs **cost_threshold**

## Goals

- Keep failures and heals low and trending down.
- Ensure cost stays well under the daily threshold most days.
- Use patterns over time to adjust thresholds safely.
