from medguard_core.proxy import message_summary


def test_provider_audit_summary_excludes_message_content():
    summary = message_summary(
        [{"role": "user", "content": "private clinical text"}]
    )

    assert summary["count"] == 1
    assert "private clinical text" not in str(summary)
