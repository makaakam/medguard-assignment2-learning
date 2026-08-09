from medguard_core.canary import collect_text


def test_nested_stream_arguments_are_collected_for_leak_checks():
    payload = {
        "choices": [
            {
                "delta": {
                    "tool_calls": [
                        {"function": {"arguments": "protected-marker"}}
                    ]
                }
            }
        ]
    }

    assert "protected-marker" in collect_text(payload)
