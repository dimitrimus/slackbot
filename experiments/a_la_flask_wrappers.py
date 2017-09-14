from functools import wraps


class A(object):
    def __init__(self):
        self._decorated_functions = []

    def param_dec(self, param):
        def dec(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                print 'xxx' + str(param)
                return fn(*args, **kwargs)

            self._decorated_functions.append(wrapper)

            return wrapper
        return dec

a = A()


@a.param_dec(param=1)
def function1():
    print 1


def function2():
    print 2


@a.param_dec(0)
def function3():
    print 3


print a._decorated_functions
a._decorated_functions[0]()
