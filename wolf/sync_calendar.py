import schedule

from wolf_core import application


class SyncCalendar(application.Application):
    def __init__(self):
        super().__init__()
        self.frequency = schedule.every(1).day.at("00:00")

    def job(self):
        self.logger.debug("SyncCalendar job started.")
        self._status = application.Status.RUNNING
        self._status = application.Status.SUCCESS
        self.logger.debug("SyncCalendar job finished with status " + str(self._status))
