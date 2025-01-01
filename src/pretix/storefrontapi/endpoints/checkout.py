import logging

from celery.result import AsyncResult
from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.translation import gettext as _
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.reverse import reverse

from pretix.base.models import Item, ItemVariation, SubEvent
from pretix.base.models.orders import CartPosition, CheckoutSession
from pretix.base.services.cart import add_items_to_cart, error_messages
from pretix.base.timemachine import time_machine_now
from pretix.presale.views.cart import generate_cart_id
from pretix.storefrontapi.permission import StorefrontEventPermission
from pretix.storefrontapi.serializers import I18nFlattenedModelSerializer

logger = logging.getLogger(__name__)


class CartAddLineSerializer(serializers.Serializer):
    item = serializers.IntegerField()
    variation = serializers.IntegerField(allow_null=True, required=False)
    subevent = serializers.IntegerField(allow_null=True, required=False)
    count = serializers.IntegerField(default=1)
    seat = serializers.CharField(allow_null=True, required=False)
    price = serializers.DecimalField(
        allow_null=True, required=False, decimal_places=2, max_digits=13
    )
    voucher = serializers.CharField(allow_null=True, required=False)


class InlineItemSerializer(I18nFlattenedModelSerializer):

    class Meta:
        model = Item
        fields = [
            "id",
            "name",
        ]


class InlineItemVariationSerializer(I18nFlattenedModelSerializer):

    class Meta:
        model = ItemVariation
        fields = [
            "id",
            "value",
        ]


class InlineSubEventSerializer(I18nFlattenedModelSerializer):

    class Meta:
        model = SubEvent
        fields = [
            "id",
            "name",
            "date_from",
        ]


class CartPositionSerializer(serializers.ModelSerializer):
    # todo: prefetch related items
    item = InlineItemSerializer(read_only=True)
    variation = InlineItemVariationSerializer(read_only=True)
    subevent = InlineSubEventSerializer(read_only=True)

    class Meta:
        model = CartPosition
        fields = [
            "item",
            "variation",
            "subevent",
            "price",
            "expires",
            # todo: attendee_name, attendee_email, voucher, addon_to, used_membership, seat, is_bundled, discount
            # todo: address, requested_valid_from
        ]


class CheckoutSessionSerializer(serializers.ModelSerializer):
    cart_positions = CartPositionSerializer(many=True)

    class Meta:
        model = CheckoutSession
        fields = [
            "cart_id",
            "sales_channel",
            "testmode",
            "cart_positions",
        ]


class CheckoutViewSet(viewsets.ViewSet):
    queryset = CheckoutSession.objects.none()
    lookup_url_kwarg = "cart_id"
    lookup_field = "cart_id"
    permission_classes = [
        StorefrontEventPermission,
    ]

    def _return_checkout_status(self, cs: CheckoutSession, status=200):
        serializer = CheckoutSessionSerializer(
            instance=cs,
            context={
                "event": self.request.event,
            },
        )
        return Response(
            serializer.data,
            status=status,
        )

    def create(self, request, *args, **kwargs):
        if (
            request.event.presale_start
            and time_machine_now() < request.event.presale_start
        ):
            raise ValidationError(error_messages["not_started"])
        if request.event.presale_has_ended:
            raise ValidationError(error_messages["ended"])

        cs = CheckoutSession.objects.create(
            event=request.event,
            cart_id=generate_cart_id(),
            sales_channel=request.sales_channel,
            testmode=request.event.testmode,
            session_data={},
        )
        return self._return_checkout_status(cs, status=201)

    def retrieve(self, request, *args, **kwargs):
        cs = get_object_or_404(
            self.request.event.checkout_sessions, cart_id=kwargs["cart_id"]
        )
        return self._return_checkout_status(cs, status=200)

    @action(detail=True, methods=["POST"])
    def add_to_cart(self, request, *args, **kwargs):
        cs = get_object_or_404(
            self.request.event.checkout_sessions, cart_id=kwargs["cart_id"]
        )
        serializer = CartAddLineSerializer(
            data=request.data.get("lines", []),
            many=True,
            context={
                "event": self.request.event,
            },
        )
        serializer.is_valid(raise_exception=True)
        return self._do_async(
            cs,
            add_items_to_cart,
            self.request.event.pk,
            serializer.validated_data,
            cs.cart_id,
            translation.get_language(),
            cs.invoice_address.pk if hasattr(cs, "invoice_address") else None,
            {},
            cs.sales_channel.identifier,
            time_machine_now(default=None),
        )

    @action(
        detail=True,
        methods=["GET"],
        url_name="task_status",
        url_path="task/(?P<asyncid>[^/]+)",
    )
    def task_status(self, *args, **kwargs):
        cs = get_object_or_404(
            self.request.event.checkout_sessions, cart_id=kwargs["cart_id"]
        )
        res = AsyncResult(kwargs["asyncid"])
        if res.ready():
            if res.successful() and not isinstance(res.info, Exception):
                return self._async_success(res, cs)
            else:
                return self._async_error(res, cs)
        return self._async_pending(res, cs)

    def _do_async(self, cs, task, *args, **kwargs):
        try:
            res = task.apply_async(args=args, kwargs=kwargs)
        except ConnectionError:
            # Task very likely not yet sent, due to redis restarting etc. Let's try once again
            res = task.apply_async(args=args, kwargs=kwargs)

        if res.ready():
            if res.successful() and not isinstance(res.info, Exception):
                return self._async_success(res, cs)
            else:
                return self._async_error(res, cs)
        return self._async_pending(res, cs)

    def _async_success(self, res, cs):
        return Response(
            {
                "status": "ok",
                "checkout_session": self._return_checkout_status(cs).data,
            },
            status=status.HTTP_200_OK,
        )

    def _async_error(self, res, cs):
        if isinstance(res.info, dict) and res.info["exc_type"] in [
            "OrderError",
            "CartError",
        ]:
            message = res.info["exc_message"]
        elif res.info.__class__.__name__ in ["OrderError", "CartError"]:
            message = str(res.info)
        else:
            logger.error("Unexpected exception: %r" % res.info)
            message = _("An unexpected error has occurred, please try again later.")

        return Response(
            {
                "status": "error",
                "message": message,
            },
            status=status.HTTP_409_CONFLICT,  # todo: find better status code
        )

    def _async_pending(self, res, cs):
        return Response(
            {
                "status": "pending",
                "check_url": reverse(
                    "storefrontapi-v1:checkoutsession-task_status",
                    kwargs={
                        "organizer": self.request.organizer.slug,
                        "event": self.request.event.slug,
                        "cart_id": cs.cart_id,
                        "asyncid": res.id,
                    },
                    request=self.request,
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )
