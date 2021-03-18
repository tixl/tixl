/*global gettext, Vue, App*/

moment.locale(document.body.attributes['data-datetimelocale'].value)
window.vapp = new Vue({
    components: {
        App: App.default
    },
    render: function (h) {
        return h('App')
    },
    data: {
        api: {
            lists: document.querySelector('#app').attributes['data-api-lists'].value,
        },
        strings: {
            'checkinlist.select': gettext('Select a check-in list'),
            'checkinlist.none': gettext('No active check-in lists found.'),
            'checkinlist.switch': gettext('Switch check-in list'),
            'results.headline': gettext('Search results'),
            'check.headline': gettext('Check-in result'),
            'scantype.switch': gettext('Switch direction'),
            'scantype.entry': gettext('Entry'),
            'scantype.exit': gettext('Exit'),
            'input.placeholder': gettext('Scan a ticket or search and press return…'),
            'pagination.next': gettext('Load more'),
            'status.p': gettext('Valid'),
            'status.n': gettext('Unpaid'),
            'status.c': gettext('Canceled'),
            'status.e': gettext('Canceled'),
            'status.redeemed': gettext('Redeemed'),
            'result.ok': gettext('Valid ticket'),
            'result.exit': gettext('Exit recorded'),
            'result.already_redeemed': gettext('Ticket already used'),
            'result.questions': gettext('Information required'),
            'result.invalid': gettext('Invalid ticket'),
            'result.product': gettext('Invalid product'),
            'result.unpaid': gettext('Ticket not paid'),
            'result.rules': gettext('Entry not allowed'),
            'result.revoked': gettext('Ticket code revoked/changed'),
            'result.canceled': gettext('Order canceled'),
        },
        event_name: document.querySelector('#app').attributes['data-event-name'].value,
        timezone: document.body.attributes['data-timezone'].value,
        datetime_format: document.body.attributes['data-datetimeformat'].value,
    },
    el: '#app'
})
