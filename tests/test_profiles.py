from autopsy.workloads.profiles import generate_prompt, get_profile


def test_generate_prompt_is_deterministic() -> None:
    profile = get_profile("short-chat")

    first = generate_prompt(profile, 3)
    second = generate_prompt(profile, 3)

    assert first.prompt == second.prompt
    assert first.prompt_family == "short-chat"
    assert first.template_id == "short-chat-v1"
    assert first.template_seed == 3
    assert first.shape["input_shape"] == "short"


def test_unknown_profile_lists_valid_profiles() -> None:
    try:
        get_profile("unknown")
    except ValueError as exc:
        assert "short-chat" in str(exc)
        assert "rag-long" in str(exc)
    else:
        raise AssertionError("Expected unknown profile to raise ValueError.")
