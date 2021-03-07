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
from django.template.defaultfilters import date as _date
from django.utils.translation import get_language, gettext_lazy as _


def daterange(df, dt):
    lng = get_language()

    if lng.startswith("de"):
        if df.year == dt.year and df.month == dt.month and df.day == dt.day:
            return "{}".format(_date(df, "j. F Y"))
        elif df.year == dt.year and df.month == dt.month:
            return "{}.–{}".format(_date(df, "j"), _date(dt, "j. F Y"))
        elif df.year == dt.year:
            return "{} – {}".format(_date(df, "j. F"), _date(dt, "j. F Y"))
    elif lng.startswith("en"):
        if df.year == dt.year and df.month == dt.month and df.day == dt.day:
            return "{}".format(_date(df, "N jS, Y"))
        elif df.year == dt.year and df.month == dt.month:
            return "{} – {}".format(_date(df, "N jS"), _date(dt, "jS, Y"))
        elif df.year == dt.year:
            return "{} – {}".format(_date(df, "N jS"), _date(dt, "N jS, Y"))
    elif lng.startswith("es"):
        if df.year == dt.year and df.month == dt.month and df.day == dt.day:
            return "{}".format(_date(df, "DATE_FORMAT"))
        elif df.year == dt.year and df.month == dt.month:
            return "{} - {} de {} de {}".format(_date(df, "j"), _date(dt, "j"), _date(dt, "F"), _date(dt, "Y"))
        elif df.year == dt.year:
            return "{} de {} - {} de {} de {}".format(_date(df, "j"), _date(df, "F"), _date(dt, "j"), _date(dt, "F"), _date(dt, "Y"))

    if df.year == dt.year and df.month == dt.month and df.day == dt.day:
        return _date(df, "DATE_FORMAT")
    return _("{date_from} – {date_to}").format(
        date_from=_date(df, "DATE_FORMAT"), date_to=_date(dt, "DATE_FORMAT")
    )
