from utils import *

class Waiter:
    events = []
    def __init__(self, timeout):
        self.timeout = timeout
        self._loop = gobject.MainLoop()

    def run(self):
        self.success = False
        self._timeout_count = 0

        self.poll()
        if self.success or self.timeout == 0:
            return self.success
        
        gobject.timeout_add_seconds(1, self._timeout_cb)
        if self.events:
            pyatspi.Registry.registerEventListener(
                self._event_cb, *self.events)
        self._loop.run()
        if self.events:
            pyatspi.Registry.deregisterEventListener(
                self._event_cb, *self.events)
        return self.success

    def _timeout_cb(self):
        if self.success: # dispose of previous waiters.
            return False
        self._timeout_count += 1
        self.poll()
        if self._timeout_count >= self.timeout or self.success:
            self._loop.quit()
            return False
        return True
    
    def poll(self):
        pass

    def _event_cb(self, event):
        self.event_cb(event)
        if self.success:
            self._loop.quit()

    def event_cb(self, event):
        pass

class NullWaiter(Waiter):
    def __init__(self, return_value, timeout):
        self._return_value = return_value
        Waiter.__init__(self, timeout)

    def run(self):
        Waiter.run(self)
        return self._return_value

class GuiExistsWaiter(Waiter):
    events = ["window:create"]
    def __init__(self, frame_name, timeout):
        Waiter.__init__(self, timeout)
        self._frame_name = frame_name
        self._desktop = pyatspi.Registry.getDesktop(0)
        self.top_level = None # Useful in subclasses

    def poll(self):
        for gui in list_guis(self._desktop):
            if match_name_to_acc(self._frame_name, gui):
                self.top_level = gui
                self.success = True

    def event_cb(self, event):
        if match_name_to_acc(self._frame_name, event.source):
            self.top_level = event.source
            self.success = True

class GuiNotExistsWaiter(Waiter):
    events = ["window:destroy"]
    def __init__(self, frame_name, timeout):
        Waiter.__init__(self, timeout)
        self._frame_name = frame_name
        self._desktop = pyatspi.Registry.getDesktop(0)

    def poll(self):
        found = False
        for gui in list_guis(self._desktop):
            if match_name_to_acc(self._frame_name, gui):
                found = True

        self.success = not found

    def event_cb(self, event):
        if match_name_to_acc(self._frame_name, event.source):
            self.success = True

class ObjectExistsWaiter(GuiExistsWaiter):
    def __init__(self, frame_name, obj_name, timeout):
        GuiExistsWaiter.__init__(self, frame_name, timeout)
        self._obj_name = obj_name

    def poll(self):
        if not self.top_level:
            GuiExistsWaiter.poll(self)
            self.success = False
        else:
            for name, obj in appmap_pairs(self.top_level):
                if name == self._obj_name:
                    self.success = True
                    break

    def event_cb(self, event):
        GuiExistsWaiter.event_cb(self, event)
        self.success = False

if __name__ == "__main__":
    waiter = ObjectExistsWaiter('frmCalculator', 'mnuEitanIsaacsonFoo', 0)
    print waiter.run()