import abc


class BaseProvider(abc.ABC):
    @abc.abstractproperty
    def routes(self):
        raise NotImplementedError

    def run_maintenance_tasks(self):
        pass
