from prometheus_client import CollectorRegistry


class IJob:
    @property
    def report_name(self):
        raise NotImplementedError()

    def report(self, registry: CollectorRegistry) -> None:
        raise NotImplementedError()
