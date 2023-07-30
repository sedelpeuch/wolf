import random
import time

import schedule

from wolf_core import application


class ExampleJob(application.Application):
    def __init__(self):
        super().__init__()
        self.frequency = schedule.every(5).seconds

    def job(self) -> application.Status:
        """
        Perform the SyncCalendar job.

        This method starts the job by setting the status to "RUNNING."
        It then sets the status to "SUCCESS" or "ERROR" randomly after a delay of 3 seconds.
        Logs the job finished with the current status.

        :return: application.Status The status of the job indicating whether it was successful or not.
        """
        self.logger.debug("Example job started.")
        time.sleep(3)
        state = random.choice([application.Status.SUCCESS, application.Status.ERROR])
        if state is application.Status.SUCCESS:
            self.set_status(state)
        else:
            a = self.logger[0]
            print(a)
        return state
