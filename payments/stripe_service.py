import stripe
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple

from django.conf import settings
from django.db import transaction

from payments.models import Payment


logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = '2026-06-24.dahlia'


class StripePaymentService:

    @staticmethod
    @transaction.atomic
    def create_payment_intent(
            user,
            amount: Decimal,
            currency: str = 'USD',
            description: str = '',
            metadata: Optional[Dict] = None,
            idempotency_key: Optional[str] = None
    ) -> Tuple[Payment, stripe.PaymentIntent]:
        if amount < Decimal('0.50'):
            raise ValueError("Мінімальна сума платежу повинна бути не менше 0.50")

        stripe_amount = int(amount * 100)  # Convert to cents
        payment_metadata = metadata or {}
        payment_metadata.update({'user_id': str(user.id)})

        try:
            logger.info(f"Creating Stripe payment intent for user {user.id} with amount {stripe_amount} {currency}")
            payment_intent_params = {
                'amount': stripe_amount,
                'currency': currency.lower(),
                'description': description,
                'metadata': payment_metadata,
                'automatic_payment_methods': {'enabled': True},
            }
            if idempotency_key:
                payment_intent_params['idempotency_key'] = idempotency_key
            payment_intent = stripe.PaymentIntent.create(**payment_intent_params)

            payment = Payment.objects.create(
                user=user,
                stripe_payment_intent_id=payment_intent.id,
                amount=amount,
                currency=currency.upper(),
                status=Payment.PaymentStatus.PENDING,
                description=description,
                metadata=payment_metadata
            )
            logger.info(f"Payment intent created successfully: {payment.id} for user {user.id}")
            return payment, payment_intent

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e.user_message}")
            raise ValueError(f"Помилка при створенні платіжного наміру: {e.user_message}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise ValueError("Сталася непередбачувана помилка при створенні платіжного наміру.")

    @staticmethod
    @transaction.atomic
    def confirm_payment(
            payment_id: str,
            stripe_payment_intent_id: str
    ) -> Payment:
        payment = Payment.objects.select_for_update().get(
            id=payment_id,
            stripe_payment_intent_id=stripe_payment_intent_id
        )

        if payment.is_successful:
            logger.info(f"Payment {payment.id} is already successful.")
            return payment

        try:
            payment_intent = stripe.PaymentIntent.retrieve(stripe_payment_intent_id)
            if payment_intent.status == 'succeeded':
                payment.status = Payment.PaymentStatus.SUCCEEDED
                payment.stripe_charge_id = payment_intent.latest_charge
                payment.save(update_fields=['status', 'stripe_charge_id', 'updated_at'])
                logger.info(f"Payment {payment.id} confirmed successfully.")
            else:
                payment.status = Payment.PaymentStatus.FAILED
                payment.error_message = f"Payment intent status: {payment_intent.status}"
                payment.save(update_fields=['status', 'error_message', 'updated_at'])
                logger.warning(f"Payment {payment.id} failed with status: {payment_intent.status}")
            return payment

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error while confirming payment {payment.id}: {e.user_message}")
            payment.status = Payment.PaymentStatus.FAILED
            payment.error_message = f"Stripe error: {e.user_message}"
            payment.save(update_fields=['status', 'error_message', 'updated_at'])
            raise ValueError(f"Помилка при підтвердженні платежу: {e.user_message}")
        except Exception as e:
            logger.error(f"Unexpected error while confirming payment {payment.id}: {str(e)}")
            payment.status = Payment.PaymentStatus.FAILED
            payment.error_message = "Сталася непередбачувана помилка при підтвердженні платежу."
            payment.save(update_fields=['status', 'error_message', 'updated_at'])
            raise ValueError("Сталася непередбачувана помилка при підтвердженні платежу.")
