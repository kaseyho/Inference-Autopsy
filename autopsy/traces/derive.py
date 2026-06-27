from autopsy.traces.schema import RequestMetrics, Timings


def derive_request_metrics(
    timings: Timings,
    token_times: list[float],
    output_tokens: int,
) -> RequestMetrics:
    itls = [
        token_times[index] - token_times[index - 1]
        for index in range(1, len(token_times))
    ]
    output_tps = None
    if output_tokens and timings.first_token is not None and timings.request_end is not None:
        generation_seconds = max((timings.request_end - timings.first_token) / 1000, 0.001)
        output_tps = output_tokens / generation_seconds

    return RequestMetrics(
        ttfb_ms=timings.first_byte,
        ttft_ms=timings.first_token,
        request_latency_ms=timings.request_end,
        itl_mean_ms=(sum(itls) / len(itls)) if itls else None,
        itl_p95_ms=percentile(itls, 0.95),
        output_tps=output_tps,
        stall_count=sum(1 for gap in itls if gap >= 500),
    )


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * p)
    return ordered[index]
