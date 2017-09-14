import time
import uuid
import datetime

from threading import Timer


class A(object):

    def __init__(self):
        self.timers = {}

    def schedule(self, period):
        def dec(fn):
            timer_id = uuid.uuid4().hex

            def wrapper():
                result = fn(datetime.datetime.now())
                if self.timers[timer_id].is_alive:
                    self.timers[timer_id] = Timer(period, wrapper, ())
                    self.timers[timer_id].start()
                return result

            self.timers[timer_id] = Timer(period, wrapper, ())
            return wrapper
        return dec

    def start(self):
        for timer in self.timers.values():
            timer.start()

    def stop(self):
        for timer in self.timers.values():
            timer.cancel()


a = A()


@a.schedule(10)
def func1(now):
    print '1 ' + str(now)


@a.schedule(6)
def func2(now):
    print '2 ' + str(now)


try:
    a.start()
    while True:
        print 2
        time.sleep(1)
except KeyboardInterrupt:
    a.stop()
