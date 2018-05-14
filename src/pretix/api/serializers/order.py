from decimal import Decimal

from django.db import transaction
from django_countries.fields import Country
from rest_framework import serializers
from rest_framework.reverse import reverse

from pretix.api.serializers.i18n import I18nAwareModelSerializer
from pretix.base.models import (
    Checkin, Invoice, InvoiceAddress, InvoiceLine, Order, OrderPosition,
    QuestionAnswer,
)
from pretix.base.models.orders import OrderFee
from pretix.base.signals import register_ticket_outputs


class CompatibleCountryField(serializers.Field):
    def to_internal_value(self, data):
        return {self.field_name: Country(data)}

    def to_representation(self, instance: InvoiceAddress):
        if instance.country:
            return str(instance.country)
        else:
            return instance.country_old


class InvoiceAddressSerializer(I18nAwareModelSerializer):
    country = CompatibleCountryField(source='*')

    class Meta:
        model = InvoiceAddress
        fields = ('last_modified', 'is_business', 'company', 'name', 'street', 'zipcode', 'city', 'country', 'vat_id',
                  'vat_id_validated', 'internal_reference')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for v in self.fields.values():
            v.required = False
            v.allow_blank = True


class AnswerQuestionIdentifierField(serializers.Field):
    def to_representation(self, instance: QuestionAnswer):
        return instance.question.identifier


class AnswerQuestionOptionsIdentifierField(serializers.Field):
    def to_representation(self, instance: QuestionAnswer):
        return [o.identifier for o in instance.options.all()]


class AnswerSerializer(I18nAwareModelSerializer):
    question_identifier = AnswerQuestionIdentifierField(source='*', read_only=True)
    option_identifiers = AnswerQuestionOptionsIdentifierField(source='*', read_only=True)

    class Meta:
        model = QuestionAnswer
        fields = ('question', 'answer', 'question_identifier', 'options', 'option_identifiers')


class CheckinSerializer(I18nAwareModelSerializer):
    class Meta:
        model = Checkin
        fields = ('datetime', 'list')


class OrderDownloadsField(serializers.Field):
    def to_representation(self, instance: Order):
        if instance.status != Order.STATUS_PAID:
            return []

        request = self.context['request']
        res = []
        responses = register_ticket_outputs.send(instance.event)
        for receiver, response in responses:
            provider = response(instance.event)
            if provider.is_enabled:
                res.append({
                    'output': provider.identifier,
                    'url': reverse('api-v1:order-download', kwargs={
                        'organizer': instance.event.organizer.slug,
                        'event': instance.event.slug,
                        'code': instance.code,
                        'output': provider.identifier,
                    }, request=request)
                })
        return res


class PositionDownloadsField(serializers.Field):
    def to_representation(self, instance: OrderPosition):
        if instance.order.status != Order.STATUS_PAID:
            return []
        if instance.addon_to_id and not instance.order.event.settings.ticket_download_addons:
            return []
        if not instance.item.admission and not instance.order.event.settings.ticket_download_nonadm:
            return []

        request = self.context['request']
        res = []
        responses = register_ticket_outputs.send(instance.order.event)
        for receiver, response in responses:
            provider = response(instance.order.event)
            if provider.is_enabled:
                res.append({
                    'output': provider.identifier,
                    'url': reverse('api-v1:orderposition-download', kwargs={
                        'organizer': instance.order.event.organizer.slug,
                        'event': instance.order.event.slug,
                        'pk': instance.pk,
                        'output': provider.identifier,
                    }, request=request)
                })
        return res


class OrderPositionSerializer(I18nAwareModelSerializer):
    checkins = CheckinSerializer(many=True)
    answers = AnswerSerializer(many=True)
    downloads = PositionDownloadsField(source='*')
    order = serializers.SlugRelatedField(slug_field='code', read_only=True)

    class Meta:
        model = OrderPosition
        fields = ('id', 'order', 'positionid', 'item', 'variation', 'price', 'attendee_name', 'attendee_email',
                  'voucher', 'tax_rate', 'tax_value', 'secret', 'addon_to', 'subevent', 'checkins', 'downloads',
                  'answers', 'tax_rule')


class OrderFeeSerializer(I18nAwareModelSerializer):
    class Meta:
        model = OrderFee
        fields = ('fee_type', 'value', 'description', 'internal_type', 'tax_rate', 'tax_value', 'tax_rule')


class OrderSerializer(I18nAwareModelSerializer):
    invoice_address = InvoiceAddressSerializer()
    positions = OrderPositionSerializer(many=True)
    fees = OrderFeeSerializer(many=True)
    downloads = OrderDownloadsField(source='*')

    class Meta:
        model = Order
        fields = ('code', 'status', 'secret', 'email', 'locale', 'datetime', 'expires', 'payment_date',
                  'payment_provider', 'fees', 'total', 'comment', 'invoice_address', 'positions', 'downloads',
                  'checkin_attention', 'last_modified')


class AnswerCreateSerializer(I18nAwareModelSerializer):

    class Meta:
        model = QuestionAnswer
        fields = ('question', 'answer', 'options')


class OrderPositionCreateSerializer(I18nAwareModelSerializer):
    answers = AnswerCreateSerializer(many=True, required=False)

    class Meta:
        model = OrderPosition
        fields = ('positionid', 'item', 'variation', 'price', 'attendee_name', 'attendee_email',
                  'tax_rule', 'secret', 'addon_to', 'subevent', 'answers')


class OrderCreateSerializer(I18nAwareModelSerializer):
    invoice_address = InvoiceAddressSerializer(required=False)
    positions = OrderPositionCreateSerializer(many=True, required=False)
    fees = OrderFeeSerializer(many=True, required=False)
    status = serializers.ChoiceField(choices=(
        ('n', Order.STATUS_PENDING),
        ('p', Order.STATUS_PAID),
    ), default='n', required=False)
    code = serializers.CharField(required=False)

    class Meta:
        model = Order
        fields = ('code', 'status', 'email', 'locale', 'payment_provider', 'fees', 'comment',
                  'invoice_address', 'positions', 'checkin_attention')

    @transaction.atomic
    def create(self, validated_data):
        fees_data = validated_data.pop('fees') if 'fees' in validated_data else []
        positions_data = validated_data.pop('positions') if 'positions' in validated_data else []
        ia = InvoiceAddress(**validated_data.pop('invoice_address'))
        order = Order(event=self.context['event'], **validated_data)
        order.set_expires(subevents=[p['subevent'] for p in positions_data])
        order.total = sum([p['price'] for p in positions_data]) + sum([f['value'] for f in fees_data], Decimal('0.00'))
        if order.total == Decimal('0.00') and validated_data.get('status') != Order.STATUS_PAID:
            order.payment_provider = 'free'
            order.status = Order.STATUS_PAID
        order.save()
        ia.order = order
        ia.save()
        for pos_data in positions_data:
            del pos_data['answers']
            order.positions.create(**pos_data)
        for fee_data in fees_data:
            order.fees.create(**fee_data)
        return order


class InlineInvoiceLineSerializer(I18nAwareModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ('description', 'gross_value', 'tax_value', 'tax_rate', 'tax_name')


class InvoiceSerializer(I18nAwareModelSerializer):
    order = serializers.SlugRelatedField(slug_field='code', read_only=True)
    refers = serializers.SlugRelatedField(slug_field='invoice_no', read_only=True)
    lines = InlineInvoiceLineSerializer(many=True)

    class Meta:
        model = Invoice
        fields = ('order', 'number', 'is_cancellation', 'invoice_from', 'invoice_to', 'date', 'refers', 'locale',
                  'introductory_text', 'additional_text', 'payment_provider_text', 'footer_text', 'lines',
                  'foreign_currency_display', 'foreign_currency_rate', 'foreign_currency_rate_date',
                  'internal_reference')
