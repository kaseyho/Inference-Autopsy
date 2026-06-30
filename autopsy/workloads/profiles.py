from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedPrompt:
    prompt: str
    prompt_family: str
    template_id: str
    template_seed: int
    shape: dict[str, int | float | str]


@dataclass(frozen=True)
class WorkloadProfile:
    name: str
    max_tokens: int
    temperature: float
    topics: tuple[str, ...]
    template: str
    input_shape: str
    output_shape: str


PROFILES = {
    "short-chat": WorkloadProfile(
        name="short-chat",
        max_tokens=128,
        temperature=0.2,
        topics=("GPU memory", "batching", "KV cache", "streaming", "latency"),
        template="Explain {topic} in one sentence.",
        input_shape="short",
        output_shape="short",
    ),
    "rag-long": WorkloadProfile(
        name="rag-long",
        max_tokens=192,
        temperature=0.2,
        topics=("GPU memory", "batching", "KV cache", "streaming", "latency"),
        template=(
            "Context:\n"
            "{topic} affects LLM serving performance. Long prompts increase "
            "prefill work. Streaming exposes token timing. Concurrency can "
            "increase queueing and tail latency.\n\n"
            "Question: Explain the most important performance risk."
        ),
        input_shape="long",
        output_shape="medium",
    ),
    "long-output": WorkloadProfile(
        name="long-output",
        max_tokens=384,
        temperature=0.2,
        topics=("GPU memory", "batching", "KV cache", "streaming", "latency"),
        template="Write a detailed explanation of how {topic} affects LLM inference.",
        input_shape="short",
        output_shape="long",
    ),
}


def get_profile(name: str) -> WorkloadProfile:
    """Return a built-in profile by name.

    Phase 3 intentionally uses a few named profiles instead of a custom profile
    file format. That keeps the first benchmark runner easy to test, explain,
    and extend later.
    """
    try:
        return PROFILES[name]
    except KeyError as exc:
        valid = ", ".join(sorted(PROFILES))
        raise ValueError(f"Unknown profile '{name}'. Valid profiles: {valid}") from exc


def generate_prompt(profile: WorkloadProfile, sequence_index: int) -> GeneratedPrompt:
    """Generate one deterministic prompt for a profile.

    The sequence index acts as the seed. This gives the benchmark controlled
    variation without random prompts that would make two runs hard to compare.
    """
    topic = profile.topics[sequence_index % len(profile.topics)]
    prompt = profile.template.format(topic=topic)

    return GeneratedPrompt(
        prompt=prompt,
        prompt_family=profile.name,
        template_id=f"{profile.name}-v1",
        template_seed=sequence_index,
        shape={
            "profile": profile.name,
            "topic": topic,
            "input_shape": profile.input_shape,
            "output_shape": profile.output_shape,
            "max_tokens": profile.max_tokens,
        },
    )
