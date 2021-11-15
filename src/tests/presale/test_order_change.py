#
# This file is part of pretix (Community Edition).
#
# Copyright (C) 2014-2020 Raphael Michel and contributors
# Copyright (C) 2020-2021 rami.io GmbH and contributors
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation in version 3 of the License.
#
# ADDITIONAL TERMS APPLY: Pursuant to Section 7 of the GNU Affero General Public License, additional terms are
# applicable granting you additional permissions and placing additional restrictions on your usage of this software.
# Please refer to the pretix LICENSE file to obtain the full terms applicable to this work. If you did not receive
# this file, see <https://pretix.eu/about/en/license>.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.  If not, see
# <https://www.gnu.org/licenses/>.
#

# This file is based on an earlier version of pretix which was released under the Apache License 2.0. The full text of
# the Apache License 2.0 can be obtained at <http://www.apache.org/licenses/LICENSE-2.0>.
#
# This file may have since been changed and any changes are released under the terms of AGPLv3 as described above. A
# full history of changes and contributors is available at <https://github.com/pretix/pretix>.
#
# This file contains Apache-licensed contributions copyrighted by: Flavia Bastos
#
# Unless required by applicable law or agreed to in writing, software distributed under the Apache License 2.0 is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

import datetime
from decimal import Decimal

from bs4 import BeautifulSoup
from django.test import TestCase
from django.utils.timezone import now
from django_scopes import scopes_disabled
from tests.base import extract_form_fields

from pretix.base.models import (
    Event, Item, ItemAddOn, ItemCategory, ItemVariation, Order, OrderPosition,
    Organizer, Question, Quota,
)
from pretix.base.models.orders import OrderPayment


class BaseOrdersTest(TestCase):

    @scopes_disabled()
    def setUp(self):
        super().setUp()
        self.orga = Organizer.objects.create(name='CCC', slug='ccc')
        self.event = Event.objects.create(
            organizer=self.orga, name='30C3', slug='30c3',
            date_from=datetime.datetime(2013, 12, 26, tzinfo=datetime.timezone.utc),
            plugins='pretix.plugins.stripe,pretix.plugins.banktransfer,tests.testdummy',
            live=True
        )
        self.event.settings.set('payment_banktransfer__enabled', True)
        self.event.settings.set('ticketoutput_testdummy__enabled', True)

        self.category = ItemCategory.objects.create(event=self.event, name="Everything", position=0)
        self.quota_shirts = Quota.objects.create(event=self.event, name='Shirts', size=2)
        self.shirt = Item.objects.create(event=self.event, name='T-Shirt', category=self.category, default_price=12)
        self.quota_shirts.items.add(self.shirt)
        self.shirt_red = ItemVariation.objects.create(item=self.shirt, default_price=14, value="Red")
        self.shirt_blue = ItemVariation.objects.create(item=self.shirt, value="Blue")
        self.quota_shirts.variations.add(self.shirt_red)
        self.quota_shirts.variations.add(self.shirt_blue)
        self.quota_tickets = Quota.objects.create(event=self.event, name='Tickets', size=5)
        self.ticket = Item.objects.create(event=self.event, name='Early-bird ticket',
                                          category=self.category, default_price=23,
                                          admission=True)
        self.quota_tickets.items.add(self.ticket)
        self.event.settings.set('attendee_names_asked', True)
        self.question = Question.objects.create(question='Foo', type=Question.TYPE_STRING, event=self.event,
                                                required=False)
        self.ticket.questions.add(self.question)

        self.order = Order.objects.create(
            status=Order.STATUS_PENDING,
            event=self.event,
            email='admin@localhost',
            datetime=now() - datetime.timedelta(days=3),
            expires=now() + datetime.timedelta(days=11),
            total=Decimal("23"),
            locale='en'
        )
        self.ticket_pos = OrderPosition.objects.create(
            order=self.order,
            item=self.ticket,
            variation=None,
            price=Decimal("23"),
            attendee_name_parts={'full_name': "Peter"}
        )
        self.deleted_pos = OrderPosition.objects.create(
            order=self.order,
            item=self.ticket,
            variation=None,
            price=Decimal("23"),
            attendee_name_parts={'full_name': "Lukas"},
            canceled=True
        )


class OrderChangeVariationTest(BaseOrdersTest):
    def test_change_not_allowed(self):
        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 302

    def test_change_variation_paid(self):
        self.event.settings.change_allow_user_variation = True
        self.event.settings.change_allow_user_price = 'any'

        with scopes_disabled():
            shirt_pos = OrderPosition.objects.create(
                order=self.order,
                item=self.shirt,
                variation=self.shirt_red,
                price=Decimal("14"),
            )
        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_blue.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            }, follow=True)
        doc = BeautifulSoup(response.content.decode(), "lxml")
        form_data = extract_form_fields(doc.select('.main-box form')[0])
        form_data['confirm'] = 'true'
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), form_data, follow=True
        )
        self.assertRedirects(response,
                             '/%s/%s/order/%s/%s/' % (self.orga.slug, self.event.slug, self.order.code,
                                                      self.order.secret),
                             target_status_code=200)
        shirt_pos.refresh_from_db()
        assert shirt_pos.variation == self.shirt_blue
        assert shirt_pos.price == Decimal('12.00')
        self.order.refresh_from_db()
        assert self.order.status == Order.STATUS_PENDING
        assert self.order.total == Decimal('35.00')

    def test_change_variation_require_higher_price(self):
        self.event.settings.change_allow_user_variation = True
        self.event.settings.change_allow_user_price = 'gt'

        with scopes_disabled():
            shirt_pos = OrderPosition.objects.create(
                order=self.order,
                item=self.shirt,
                variation=self.shirt_red,
                price=Decimal("14"),
            )
        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_blue.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            }, follow=True)
        assert response.status_code == 200
        assert 'alert-danger' in response.content.decode()

        shirt_pos.variation = self.shirt_blue
        shirt_pos.price = Decimal('12.00')
        shirt_pos.save()

        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret),
            {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_red.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            },
            follow=True
        )
        doc = BeautifulSoup(response.content.decode(), "lxml")
        form_data = extract_form_fields(doc.select('.main-box form')[0])
        form_data['confirm'] = 'true'
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), form_data, follow=True
        )
        self.assertRedirects(response,
                             '/%s/%s/order/%s/%s/' % (self.orga.slug, self.event.slug, self.order.code,
                                                      self.order.secret),
                             target_status_code=200)
        shirt_pos.refresh_from_db()
        assert shirt_pos.variation == self.shirt_red
        assert shirt_pos.price == Decimal('14.00')
        self.order.refresh_from_db()
        assert self.order.status == Order.STATUS_PENDING
        assert self.order.total == Decimal('37.00')

        shirt_pos.variation = self.shirt_blue
        shirt_pos.price = Decimal('14.00')
        shirt_pos.save()

        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret),
            {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_red.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            },
            follow=True
        )
        shirt_pos.refresh_from_db()
        assert 'alert-danger' in response.content.decode()
        assert shirt_pos.variation == self.shirt_blue
        assert shirt_pos.price == Decimal('14.00')

    def test_change_variation_require_higher_equal_price(self):
        self.event.settings.change_allow_user_variation = True
        self.event.settings.change_allow_user_price = 'gte'

        with scopes_disabled():
            shirt_pos = OrderPosition.objects.create(
                order=self.order,
                item=self.shirt,
                variation=self.shirt_red,
                price=Decimal("14"),
            )
        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_blue.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            }, follow=True)
        assert response.status_code == 200
        assert 'alert-danger' in response.content.decode()

        shirt_pos.variation = self.shirt_blue
        shirt_pos.price = Decimal('12.00')
        shirt_pos.save()

        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret),
            {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_red.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            },
            follow=True
        )
        doc = BeautifulSoup(response.content.decode(), "lxml")
        form_data = extract_form_fields(doc.select('.main-box form')[0])
        form_data['confirm'] = 'true'
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), form_data, follow=True
        )
        self.assertRedirects(response,
                             '/%s/%s/order/%s/%s/' % (self.orga.slug, self.event.slug, self.order.code,
                                                      self.order.secret),
                             target_status_code=200)
        shirt_pos.refresh_from_db()
        assert shirt_pos.variation == self.shirt_red
        assert shirt_pos.price == Decimal('14.00')
        self.order.refresh_from_db()
        assert self.order.status == Order.STATUS_PENDING
        assert self.order.total == Decimal('37.00')

        shirt_pos.variation = self.shirt_blue
        shirt_pos.price = Decimal('14.00')
        shirt_pos.save()

        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret),
            {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_red.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            },
            follow=True
        )
        doc = BeautifulSoup(response.content.decode(), "lxml")
        form_data = extract_form_fields(doc.select('.main-box form')[0])
        form_data['confirm'] = 'true'
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), form_data, follow=True
        )
        shirt_pos.refresh_from_db()
        assert 'alert-success' in response.content.decode()
        assert shirt_pos.variation == self.shirt_red
        assert shirt_pos.price == Decimal('14.00')

    def test_change_variation_require_equal_price(self):
        self.event.settings.change_allow_user_variation = True
        self.event.settings.change_allow_user_price = 'eq'

        with scopes_disabled():
            shirt_pos = OrderPosition.objects.create(
                order=self.order,
                item=self.shirt,
                variation=self.shirt_blue,
                price=Decimal("12"),
            )
        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_red.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            }, follow=True)
        assert response.status_code == 200
        assert 'alert-danger' in response.content.decode()

    def test_change_variation_require_same_product(self):
        self.event.settings.change_allow_user_variation = True
        self.event.settings.change_allow_user_price = 'any'

        with scopes_disabled():
            shirt_pos = OrderPosition.objects.create(
                order=self.order,
                item=self.shirt,
                variation=self.shirt_blue,
                price=Decimal("12"),
            )
        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), {
                f'op-{shirt_pos.pk}-itemvar': f'{self.ticket.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            }, follow=True)
        assert response.status_code == 200
        assert 'alert-danger' in response.content.decode()

    def test_change_variation_require_quota(self):
        self.event.settings.change_allow_user_variation = True
        self.event.settings.change_allow_user_price = 'any'

        with scopes_disabled():
            q = self.event.quotas.create(name="s2", size=0)
            q.items.add(self.shirt)
            q.variations.add(self.shirt_red)

        with scopes_disabled():
            shirt_pos = OrderPosition.objects.create(
                order=self.order,
                item=self.shirt,
                variation=self.shirt_blue,
                price=Decimal("12"),
            )
        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_red.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            }, follow=True)
        assert response.status_code == 200
        assert 'alert-danger' in response.content.decode()

        q.variations.add(self.shirt_blue)

        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_red.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            }, follow=True)
        doc = BeautifulSoup(response.content.decode(), "lxml")
        form_data = extract_form_fields(doc.select('.main-box form')[0])
        form_data['confirm'] = 'true'
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), form_data, follow=True
        )
        self.assertRedirects(response,
                             '/%s/%s/order/%s/%s/' % (self.orga.slug, self.event.slug, self.order.code,
                                                      self.order.secret),
                             target_status_code=200)
        shirt_pos.refresh_from_db()
        assert shirt_pos.variation == self.shirt_red
        assert shirt_pos.price == Decimal('14.00')

    def test_change_paid_to_pending(self):
        self.event.settings.change_allow_user_variation = True
        self.event.settings.change_allow_user_price = 'any'
        self.order.status = Order.STATUS_PAID
        self.order.save()

        with scopes_disabled():
            self.order.payments.create(provider="manual", amount=Decimal('35.00'), state=OrderPayment.PAYMENT_STATE_CONFIRMED)
            shirt_pos = OrderPosition.objects.create(
                order=self.order,
                item=self.shirt,
                variation=self.shirt_blue,
                price=Decimal("12"),
            )

        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret),
            {
                f'op-{shirt_pos.pk}-itemvar': f'{self.shirt.pk}-{self.shirt_red.pk}',
                f'op-{self.ticket_pos.pk}-itemvar': f'{self.ticket.pk}',
            },
            follow=True
        )
        doc = BeautifulSoup(response.content.decode(), "lxml")
        form_data = extract_form_fields(doc.select('.main-box form')[0])
        form_data['confirm'] = 'true'
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), form_data, follow=True
        )
        self.assertRedirects(response,
                             '/%s/%s/order/%s/%s/pay/change' % (self.orga.slug, self.event.slug, self.order.code,
                                                                self.order.secret),
                             target_status_code=200)
        assert 'The order has been changed. You can now proceed by paying the open amount of €2.00.' in response.content.decode()
        shirt_pos.refresh_from_db()
        assert shirt_pos.variation == self.shirt_red
        assert shirt_pos.price == Decimal('14.00')
        self.order.refresh_from_db()
        assert self.order.status == Order.STATUS_PENDING
        assert self.order.pending_sum == Decimal('2.00')


class OrderChangeAddonsTest(BaseOrdersTest):

    @scopes_disabled()
    def setUp(self):
        super().setUp()

        self.workshopcat = ItemCategory.objects.create(name="Workshops", is_addon=True, event=self.event)
        self.workshopquota = Quota.objects.create(event=self.event, name='Workshop 1', size=5)
        self.workshop1 = Item.objects.create(event=self.event, name='Workshop 1',
                                             category=self.workshopcat, default_price=Decimal('12.00'))
        self.workshop2 = Item.objects.create(event=self.event, name='Workshop 2',
                                             category=self.workshopcat, default_price=Decimal('12.00'))
        self.workshop2a = ItemVariation.objects.create(item=self.workshop2, value='A')
        self.workshop2b = ItemVariation.objects.create(item=self.workshop2, value='B')
        self.workshopquota.items.add(self.workshop1)
        self.workshopquota.items.add(self.workshop2)
        self.workshopquota.variations.add(self.workshop2a)
        self.workshopquota.variations.add(self.workshop2b)
        self.iao = ItemAddOn.objects.create(
            base_item=self.ticket, addon_category=self.workshopcat, max_count=1, min_count=0, multi_allowed=False
        )
        self.event.settings.change_allow_user_addons = True

    def test_no_change(self):
        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        assert 'Workshop 1' in response.content.decode()

        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret),
            {
            },
            follow=True
        )
        assert 'alert-info' in response.content.decode()

    def test_add_addon(self):
        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        assert 'Workshop 1' in response.content.decode()

        doc = BeautifulSoup(response.content.decode(), "lxml")
        assert doc.select(f'input[name=cp_{self.ticket_pos.pk}_item_{self.workshop1.pk}]')

        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret),
            {
                f'cp_{self.ticket_pos.pk}_item_{self.workshop1.pk}': '1'
            },
            follow=True
        )
        doc = BeautifulSoup(response.content.decode(), "lxml")
        form_data = extract_form_fields(doc.select('.main-box form')[0])
        form_data['confirm'] = 'true'
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), form_data, follow=True
        )
        assert 'alert-success' in response.content.decode()

        with scopes_disabled():
            new_pos = self.ticket_pos.addons.get()
            assert new_pos.item == self.workshop1
            assert new_pos.price == Decimal('12.00')
            self.order.refresh_from_db()
            assert self.order.total == Decimal('35.00')

    def test_remove_addon(self):
        with scopes_disabled():
            OrderPosition.objects.create(
                order=self.order,
                item=self.workshop1,
                variation=None,
                price=Decimal("12"),
                addon_to=self.ticket_pos,
                attendee_name_parts={'full_name': "Peter"}
            )
            self.order.total += Decimal("12")
            self.order.save()

        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        assert 'Workshop 1' in response.content.decode()

        doc = BeautifulSoup(response.content.decode(), "lxml")
        assert doc.select(f'input[name=cp_{self.ticket_pos.pk}_item_{self.workshop1.pk}]')[0].attrs['checked']

        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret),
            {
            },
            follow=True
        )
        doc = BeautifulSoup(response.content.decode(), "lxml")
        form_data = extract_form_fields(doc.select('.main-box form')[0])
        form_data['confirm'] = 'true'
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), form_data, follow=True
        )
        assert 'alert-success' in response.content.decode()

        with scopes_disabled():
            a = self.ticket_pos.addons.get()
            assert a.canceled
            self.order.refresh_from_db()
            assert self.order.total == Decimal('23.00')

    def test_change_addon(self):
        with scopes_disabled():
            OrderPosition.objects.create(
                order=self.order,
                item=self.workshop1,
                variation=None,
                price=Decimal("12"),
                addon_to=self.ticket_pos,
                attendee_name_parts={'full_name': "Peter"}
            )
            self.order.total += Decimal("12")
            self.order.save()

        response = self.client.get(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret)
        )
        assert response.status_code == 200
        assert 'Workshop 1' in response.content.decode()

        doc = BeautifulSoup(response.content.decode(), "lxml")
        assert doc.select(f'input[name=cp_{self.ticket_pos.pk}_item_{self.workshop1.pk}]')[0].attrs['checked']

        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret),
            {
                f'cp_{self.ticket_pos.pk}_variation_{self.workshop2.pk}_{self.workshop2a.pk}': '1'
            },
            follow=True
        )
        doc = BeautifulSoup(response.content.decode(), "lxml")
        form_data = extract_form_fields(doc.select('.main-box form')[0])
        form_data['confirm'] = 'true'
        response = self.client.post(
            '/%s/%s/order/%s/%s/change' % (self.orga.slug, self.event.slug, self.order.code, self.order.secret), form_data, follow=True
        )
        assert 'alert-success' in response.content.decode()

        with scopes_disabled():
            # todo: should this keep questions?
            a = self.ticket_pos.addons.get(canceled=False)
            assert a.item == self.workshop2
            assert a.variation == self.workshop2a

    # test_new_payment_deadline
    # test_not_allowed_if_no_addons
    # test_required_questions
    # test_quota_sold_out
    # test_quota_sold_out_replace
    # test_voucher_required
    # test_forbidden_sales_channel
    # test_forbidden_not_available
    # test_forbidden_disabled_for_subevent
    # test_forbidden_require_bundling
    # test_presale_has_ended
    # test_last_payment_term
    # test_addon_count_constraints
    # test_addon_multi
    # test_variation_change_and_addon_change
    # test_allow_user_price_gte
    # test_allow_user_price_gt
    # test_allow_user_price_eq
    # test_do_not_include_bundled
    # test_refund
