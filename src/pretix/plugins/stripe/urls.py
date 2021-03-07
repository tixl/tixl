#
# This file is part of pretix Community.
#
# Copyright (C) 2014-2020 Raphael Michel and contributors
# Copyright (C) 2020-2021 rami.io GmbH and contributors
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation in version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.  If not, see
# <https://www.gnu.org/licenses/>.
#
# ADDITIONAL TERMS: Pursuant to Section 7 of the GNU Affero General Public License, additional terms are applicable
# granting you additional permissions and placing additional restrictions on your usage of this software. Please refer
# to the pretix LICENSE file to obtain the full terms applicable to this work. If you did not receive this file, see
# <https://pretix.eu/about/en/license>.
#
from django.conf.urls import include, url

from pretix.multidomain import event_url

from .views import (
    OrganizerSettingsFormView, ReturnView, ScaReturnView, ScaView,
    applepay_association, oauth_disconnect, oauth_return, redirect_view,
    webhook,
)

event_patterns = [
    url(r'^stripe/', include([
        event_url(r'^webhook/$', webhook, name='webhook', require_live=False),
        url(r'^redirect/$', redirect_view, name='redirect'),
        url(r'^return/(?P<order>[^/]+)/(?P<hash>[^/]+)/(?P<payment>[0-9]+)/$', ReturnView.as_view(), name='return'),
        url(r'^sca/(?P<order>[^/]+)/(?P<hash>[^/]+)/(?P<payment>[0-9]+)/$', ScaView.as_view(), name='sca'),
        url(r'^sca/(?P<order>[^/]+)/(?P<hash>[^/]+)/(?P<payment>[0-9]+)/return/$',
            ScaReturnView.as_view(), name='sca.return'),
    ])),
    url(r'^.well-known/apple-developer-merchantid-domain-association$',
        applepay_association, name='applepay.association'),
]

organizer_patterns = [
    url(r'^.well-known/apple-developer-merchantid-domain-association$',
        applepay_association, name='applepay.association'),
]

urlpatterns = [
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/stripe/disconnect/',
        oauth_disconnect, name='oauth.disconnect'),
    url(r'^control/organizer/(?P<organizer>[^/]+)/stripeconnect/',
        OrganizerSettingsFormView.as_view(), name='settings.connect'),
    url(r'^_stripe/webhook/$', webhook, name='webhook'),
    url(r'^_stripe/oauth_return/$', oauth_return, name='oauth.return'),
    url(r'^.well-known/apple-developer-merchantid-domain-association$',
        applepay_association, name='applepay.association'),
]
