#!/usr/bin/env python
# encoding: utf-8

"""
pydispatcher demo
requirements: pip install pydispatcher
"""

from pydispatch import dispatcher    # type: ignore

ORDER_CREATED_SIGNAL = 'order.created'
ORDER_STATUS_CHANGED_SIGNAL = 'order.status_changed'


class Order(object):
    def __init__(self, number):
        self.number = number
        self.status = 'PENDING'

    def __repr__(self):
        return "{} [{}]".format(
            self.number,
            self.status
        )

    def __str__(self):
        return "{} [{}]".format(
            self.number,
            self.status
        )

    def __unicode__(self):
        return u"{} [{}]".format(
            self.number,
            self.status
        )


class OrderService(object):
    """Order Service"""

    def createOrder(self, number):
        order = Order(number)
        dispatcher.send(
            signal=ORDER_CREATED_SIGNAL, sender=self, order=order
        )
        return order

    def closeOrder(self, order):
        order.status = 'CLOSED'
        dispatcher.send(
            signal=ORDER_STATUS_CHANGED_SIGNAL, sender=self, order=order
        )
        return order

    def __repr__(self):
        return self.__doc__

    def __str__(self):
        return self.__doc__

    def __unicode__(self):
        return self.__doc__


# debug listener, prints sender and params
def debug_listener(sender, **kwargs):

    print("[DEBUG] '{}' sent data '{}'".format(
        sender,
        ", ".join([
            "{} => {}".format(key, value) for key, value in kwargs.items()
        ])
    ))


# send email listener
def send_order_email_listener(sender, order):
    print("[MAIL] '{}' sending email about order '{}'".format(sender, order))


# send email every time when order is created
dispatcher.connect(
    send_order_email_listener,
    signal=ORDER_CREATED_SIGNAL,
    sender=dispatcher.Any
)

# debug all signals
dispatcher.connect(
    debug_listener,
    signal=ORDER_CREATED_SIGNAL,
    sender=dispatcher.Any
)

dispatcher.connect(
    debug_listener,
    signal=ORDER_STATUS_CHANGED_SIGNAL,
    sender=dispatcher.Any
)


# let's go
# s = OrderService()
# o1 = s.createOrder('1234/Z/12')
# o2 = s.createOrder('1234/A/12')
# s.closeOrder(o2)
# s.closeOrder(o1)
print('========================================================================================\n')




# Test the creation of an order
def test_create_order():
    order_service = OrderService()
    order = order_service.createOrder('1234/Z/12')
    assert isinstance(order, Order)
    assert order.number == '1234/Z/12'
    assert order.status == 'PENDING'


# Test the closing of an order:
def test_close_order():
    order_service = OrderService()
    order = order_service.createOrder('1234/Z/12')
    order_service.closeOrder(order)
    assert order.status == 'CLOSED'


# Test the signal emission when creating an order:
def test_order_created_signal():
    order_service = OrderService()
    order = None

    def order_created_listener(sender, **kwargs):
        nonlocal order
        order = kwargs.get('order')

    dispatcher.connect(
        order_created_listener,
        signal=ORDER_CREATED_SIGNAL,
        sender=dispatcher.Any
    )

    order_service.createOrder('1234/Z/12')
    assert isinstance(order, Order)
    assert order.number == '1234/Z/12'
    assert order.status == 'PENDING'


# Test the signal emission when closing an order:
def test_order_status_changed_signal():
    order_service = OrderService()
    order = order_service.createOrder('1234/Z/12')
    order_status = None

    def order_status_changed_listener(sender, **kwargs):
        nonlocal order_status
        order_status = kwargs.get('order').status

    dispatcher.connect(
        order_status_changed_listener,
        signal=ORDER_STATUS_CHANGED_SIGNAL,
        sender=dispatcher.Any
    )

    order_service.closeOrder(order)
    assert order_status == 'CLOSED'


# Test the debug listener:
def test_debug_listener():
    order_service = OrderService()
    debug_output = []

    def debug_listener(sender, **kwargs):
        debug_output.append(kwargs)

    dispatcher.connect(
        debug_listener,
        signal=ORDER_CREATED_SIGNAL,
        sender=dispatcher.Any
    )

    order_service.createOrder('1234/Z/12')
    assert len(debug_output) == 1
    assert debug_output[0].get('order').number == '1234/Z/12'
    assert debug_output[0].get('order').status == 'PENDING'





test_create_order()
print('========================================================================================\n')

test_close_order()
print('========================================================================================\n')

test_order_created_signal()
print('========================================================================================\n')

test_order_status_changed_signal()
print('========================================================================================\n')

test_debug_listener()
print('========================================================================================\n')