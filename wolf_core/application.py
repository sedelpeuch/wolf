#! /usr/bin/env python3
"""
This module contains the Application Interface of the core module.
All applications must implement this interface if they want to be run by the runner.
"""
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import List

import schedule

from wolf_core import api


class Status(Enum):
    """
    This class is an enum for the status of an application.
    """

    NEVER = 0
    RUNNING = 1
    WAITING = 2
    ERROR = 3
    SUCCESS = 4

    def __str__(self):
        """
        This method returns the name of the status.
        :return: The name of the status.
        """
        return self.name


class Application(ABC):
    """
    Application Interface of the core module.
    All applications must implement this interface if they want to be run by the runner.

    An application can use one or more APIs to work.
    The APIs are stored in a list.
    The frequency of the application is stored in a schedule.Job.

    The job method is the method that is called by the runner.
    It must be implemented by the application.
    This method must contain all the work of
    the application.

    :ivar _apis: The list of APIs used by the application.
    :see: :class:`api.API`
    :type _apis: List[api.API]

    :ivar frequency: The frequency of the application.
    :see: :class:`schedule.Job`
    :type frequency: schedule.Job
    """

    def __init__(self):
        self._apis: List[api.API] = api.API.instances
        self.frequency: schedule.Job = schedule.every().day
        self.logger = logging.getLogger(__name__)

        self.__health_check = {"status": Status.WAITING, "message": " ", "last_execution": Status.NEVER, "id": -1, }

        self.app_lock = threading.Lock()
        self.__debug = False

    @property
    def health_check(self):
        """
        This property returns the health check of the application.

        :return: The health check of the application
        :rtype: bool
        :raises: None
        """
        return self.__health_check

    @health_check.setter
    def health_check(self, value):
        """
        This method sets the health check of the application.

        :param value: A dictionary representing the health check information.
        :return: None
        """
        if not isinstance(value, dict):
            raise TypeError("The health check must be a dict.")
        try:
            self.__health_check["status"] = value["status"]
        except KeyError:
            pass
        try:
            self.__health_check["message"] = value["message"]
        except KeyError:
            pass
        try:
            self.__health_check["last_execution"] = value["last_execution"]
        except KeyError:
            pass
        try:
            self.__health_check["id"] = value["id"]
        except KeyError:
            pass

    @property
    def status(self) -> Status:
        """
        This property returns the status of the application.

        :return: The status of the application.
        :rtype: Status.
        """
        return self.__health_check["status"]

    def set_status(self, value: Status):
        """
        This method sets the status of the application.

        :param value: The status value to be set.
        Must be of type Status.
        :return: None
        """
        if not isinstance(value, Status):
            raise TypeError("The status must be a Status.")
        self.health_check = {"status": value}

    @property
    def debug(self) -> bool:
        """
        This property returns the debug mode of the application.

        :return: The debug mode of the application as a boolean value.
        """
        return self.__debug

    @debug.setter
    def debug(self, value: bool):
        """
        This method sets the debug mode of the application.

        :param value: A boolean value indicating whether debug mode should be enabled or disabled.
        :return: None
        """
        if not isinstance(value, bool):
            raise TypeError("The debug mode must be a boolean.")
        self.__debug = value

    def api(self, name):
        """
        This method returns the API with the given name.

        :param name: The name of the API.
        :return: The API object corresponding to the given name.
        :raises ValueError: If the API with the given name does not exist.
        """
        for api_object in self._apis:
            if api_object.__class__.__name__ == name:
                return api_object
        raise ValueError("The API with name {} does not exist.".format(name))

    def run(self):
        """
        The runner calls this method.
        It loads the APIs, sets the frequency and schedules the job.

        This method must not be overridden.
        :return: None
        """
        self.app_lock.acquire()
        self.health_check = {"status": Status.RUNNING, "id": uuid.uuid4().int, "message": " ", }
        state = Status.RUNNING
        try:
            state = self.job()
        except Exception as e:
            self.health_check = {"status": Status.ERROR, "message": str(e)}
            state = Status.ERROR
            self.logger.error("An error occurred while running the application: {} - {}".format(type(e).__name__, e))
            if self.__debug:
                raise e
        finally:
            self.health_check = {"last_execution": self.status, "status": state}
        self.app_lock.release()

    @abstractmethod
    def job(self) -> Status:
        """
        The runner calls this method.
        It must contain all the work of the application.
        It must update the status of the application (RUNNING, ERROR, SUCCESS).

        :return: None
        """
        pass

    def shutdown(self):
        """
        The runner calls this method when the application is stopped.
        It must stop all the work of the application.

        :return: None
        """
        pass
