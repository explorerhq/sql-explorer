## Testing helpers (from http://stackoverflow.com/a/3829849/221390
class AssertMethodIsCalled(object):
    def __init__(self, obj, method):
        self.obj = obj
        self.method = method

    def called(self, *args, **kwargs):
        self.method_called = True
        self.orig_method(*args, **kwargs)

    def __enter__(self):
        self.orig_method = getattr(self.obj, self.method)
        setattr(self.obj, self.method, self.called)
        self.method_called = False

    def __exit__(self, exc_type, exc_value, traceback):
        assert getattr(self.obj, self.method) == self.called, "method %s was modified during assertMethodIsCalled" % self.method

        setattr(self.obj, self.method, self.orig_method)

        # If an exception was thrown within the block, we've already failed.
        if traceback is None:
            assert self.method_called, "method %s of %s was not called" % (self.method, self.obj)