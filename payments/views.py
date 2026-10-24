import logging
from decimal import Decimal

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from payments.models import Payment
from payments.stripe_service import StripePaymentService
from payments.serializers import PaymentSerializer, CreatePaymentSerializer
from shop.orders.models import Order
from payments.utils import send_reciepe


logger = logging.getLogger(__name__)

STRIPE_P_KEY = settings.STRIPE_PUBLISHABLE_KEY


def checkout_view(request, order_id=None):
    order = None
    if order_id:
        order = get_object_or_404(Order, id=order_id)
    return render(request, 'checkout.html', {
        'stripe_publishable_key': STRIPE_P_KEY,
        'order': order,
    })


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).select_related('user')

    def get_serializer_class(self):
        if self.action == 'create_payment_intent':
            return CreatePaymentSerializer
        return PaymentSerializer

    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment, payment_intent = StripePaymentService.create_payment_intent(
                user=request.user,
                amount=Decimal(serializer.validated_data['amount']),
                currency=serializer.validated_data['currency'],
                description=serializer.validated_data.get('description', ''),
                metadata=serializer.validated_data.get('metadata', {})
            )
            return Response({
                "payment_id": str(payment.id),
                "client_secret": payment_intent.client_secret,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "status": payment.status,
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            logger.error(f"Error creating payment intent: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {e}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        payment = self.get_object()
        order_id = request.query_params.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        if order:
            order.status = Order.OrderStatus.PAID
            order.payment = payment
            order.save()
        else:
            order = None

        try:
            StripePaymentService.confirm_payment(
                payment_id=str(payment.id),
                stripe_payment_intent_id=payment.stripe_payment_intent_id
            )
            serializer = self.get_serializer(payment)
            send_reciepe(payment.user.email, order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.error(f"Error confirming payment: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error confirming payment: {e}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
