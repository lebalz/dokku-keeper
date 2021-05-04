
class IJob:
    @property
    def report_name(self):
        raise NotImplementedError()

    def report(self) -> None:
        raise NotImplementedError()
