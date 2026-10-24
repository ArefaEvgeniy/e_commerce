import pytest
from unittest.mock import patch

from payments.utils import send_reciepe
from payments.utils import calculate_interest


@pytest.mark.parametrize(
    "amount, interest_rate, months, expected",
    [
        (1000, 0.05, 1, 1050),
        (1000, 0.05, 2, 1102.5),
        (1000, 0.10, 3, 1331),
        (500, 0.02, 1, 510),
    ],
)
def test_calculate_interest(amount, interest_rate, months, expected):
    assert calculate_interest(amount, interest_rate, months) == expected


@pytest.mark.parametrize(
    "amount, interest_rate, months, expected",
    [
        (0, 0.05, 1, 0),
        (1000, 0, 2, 1000),
        (1000, 0.10, 0, 1000),
    ],
)
def test_calculate_interest_edge_cases(amount, interest_rate, months, expected):
    assert calculate_interest(amount, interest_rate, months) == expected


@pytest.mark.xfail()
def test_calculate_interest_negative_case():
    assert calculate_interest(1000, 0.2, -1) == 1000


@patch("payments.utils.EmailMultiAlternatives")
def test_send_reciepe(mock_email_class):
    order = 123
    email = "test@example.com"

    send_reciepe(email, order)

    mock_email_class.assert_called_once_with(
        subject="Замовлення #123",
        from_email=None,
        to=["test@example.com"],
    )

    mock_email = mock_email_class.return_value
    mock_email.send.assert_called_once()
