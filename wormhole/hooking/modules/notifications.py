from .base import BaseModule


class Observer:
    def __init__(self, name, sel):
        self.name = name
        self.selector = sel

    def __repr__(self):
        return f"{self.name} ({self.selector})"


class Notifications(BaseModule):
    """
    This module is used to collect, process and aggregate the results of notifications functions hooking.
    Hooked functions:
        +[NSNotificationCenter postNotificationName:object:userInfo:]
        -[NSNotificationCenter addObserver:selector:name:object:]
        - CFNotificationCenterPostNotification
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        self.registered_nots = {}
        self.not_observer = {}

    def _process(self):
        if self.message.symbol == "notify_register_dispatch":
            self.registered_nots[self.message.args[1]] = self.message.args[0]
            self.publish(f"{self.message.args[1]} - {self.message.args[0]}")
        elif self.message.symbol == "notify_cancel":
            try:
                self.publish(
                    f"{int(self.message.args[0], 16)} - {self.registered_nots[int(self.message.args[0], 16)]} >> X")
                del self.registered_nots[int(self.message.args[0], 16)]
            except KeyError:
                pass
        elif self.message.symbol == "notify_post":
            self.publish(f">> {self.message.args[0]}")
        elif "addObserver:selector:name:object:" in self.message.symbol:
            if not self.message.args[0].startswith("UI") and not self.message.args[0].startswith("_UI") and \
                    not self.message.args[0].startswith("NS") and not self.message.args[0].startswith("_NS"):
                observers = self.not_observer.get(self.message.args[0], set())
                if observers:
                    # observers.add(Observer(self.message.args[2], self.message.args[1]))
                    observers.add(self.message.args[2])
                else:
                    # observers.add(Observer(self.message.args[2], self.message.args[1]))
                    observers.add(self.message.args[2])
                    self.not_observer[self.message.args[0]] = observers
        elif "postNotificationName:object:userInfo:" in self.message.symbol:
            if not self.message.args[0].startswith("UI") and not self.message.args[0].startswith("_UI") and \
                    not self.message.args[0].startswith("NS") and not self.message.args[0].startswith("_NS"):
                self.publish(f"{self.message.args[0]} ({self.message.args[1]} -- {self.message.args[2]}) >>"
                             f" {self.not_observer.get(self.message.args[0], '')}")
        elif "removeObserver:name:object:" in self.message.symbol:
            observers = self.not_observer.get(self.message.args[0], set())
            if observers:
                observers.remove(self.message.args[1])
        elif "CFNotificationCenterPostNotification" in self.message.symbol:
            self.publish(f"{self.message.args[0]} ({self.message.args[1]} -- {self.message.args[2]}) >>"
                         f" {self.not_observer.get(self.message.args[0], '')}")
        else:
            print(self.message.args)
            self.publish(self.message.args)
