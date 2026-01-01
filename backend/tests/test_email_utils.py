from backend.services.email_utils import normalize_sender


def test_normalize_sender_standard():
    assert (
        normalize_sender("John Doe <john@example.com>") == "John Doe <john@example.com>"
    )
    assert normalize_sender("john@example.com") == "john@example.com"


def test_normalize_sender_apple_relay_peloton():
    raw = '"Peloton" <peloton_at_mail_op_onepeloton_com_k6myg754kg_192d3661@privaterelay.appleid.com>'
    expected = "Peloton <peloton@mail.op.onepeloton.com>"
    assert normalize_sender(raw) == expected


def test_normalize_sender_apple_relay_indeed():
    raw = '"Indeed" <donotreply_at_match_indeed_com_7dtpcj9p77_c32249dc@privaterelay.appleid.com>'
    expected = "Indeed <donotreply@match.indeed.com>"
    assert normalize_sender(raw) == expected


def test_normalize_sender_apple_relay_no_name():
    raw = (
        "peloton_at_mail_op_onepeloton_com_k6myg754kg_192d3661@privaterelay.appleid.com"
    )
    expected = "peloton@mail.op.onepeloton.com"
    assert normalize_sender(raw) == expected


def test_normalize_sender_malformed():
    assert normalize_sender(None) == ""
    assert normalize_sender("") == ""
    assert normalize_sender("plain_string") == "plain_string"
