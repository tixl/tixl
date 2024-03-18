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
import logging

from django import template
from django.core.files.storage import default_storage

from pretix._base_settings import PILLOW_FORMATS_QUESTIONS_FAVICON
from pretix.helpers.thumb import get_thumbnail

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def thumb(source, arg):
    try:
        return get_thumbnail(source, arg).thumb.url
    except:
        logger.exception(f'Failed to create thumbnail of {source}')
        # HACK: source.url works for some types of files (e.g. FieldFile), and for all files retrieved from Hierarkey,
        # default_storage.url works for all files in NanoCDNStorage. For others, this may return an invalid URL.
        # But for a fallback, this can probably be accepted.
        return source.url if hasattr(source, 'url') else default_storage.url(source.name)


@register.filter
def favicon_thumb(source, arg):
    try:
        return get_thumbnail(source, arg, formats=PILLOW_FORMATS_QUESTIONS_FAVICON).thumb.url
    except:
        logger.exception(f'Failed to create thumbnail of {source}')
        return source.url if hasattr(source, 'url') else default_storage.url(source.name)
