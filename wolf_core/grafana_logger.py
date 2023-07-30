#! /usr/bin/env python3
"""
The GrafanaLogger class of the provided Python code creates a connection to a MySQL database
and enables the logging of messages into a specific table.
It primarily comprises three methods:

__init__(self, logger=None): Constructor method for the class.
It initializes several instance variables, including the database name,
table name, prepares the database schema, and a logger object for event logging.
It also calls the private method __create_use_db
which connects to a database and establishes a table for logging operations.

__create_use_db(self):
This private method creates the database connection
and attempts to create the specified table if it doesn't already exist.
If the table exists, the method attempts to drop it before creating a new one.
It prepares the cursor for executing subsequent queries.

post (self, job, status, message): This method registers a log message to the table defined earlier.
It formulates the SQL query to insert a new row into the table,
utilizing user-provided values for fields (job, status, and message) and the current timestamp.
"""
import datetime
import threading

import mysql.connector


class GrafanaLogger:
    """
    The GrafanaLogger class allows posting log messages to a MySQL database.

    Attributes:
        __dbName (str): The name of the database.
        __tableName (str): The name of the table.
        __db (mysql.connector.MySQLConnection): The database connection.
        __logger: The logger object for logging events.
        __database_schema (str): The schema for creating the table.
        post_lock (threading.Lock): The lock used for thread safety.

    Methods:
        __init__(self, logger=None):
            Initializes the GrafanaLogger instance.

        __create_use_db(self):
            Tries to create the database with the name specified in __dbName.
            If the database already exists, it uses it and sets the cursor.

        post (self, job, status, message):
             Post a log message to the database.
    """

    def __init__(self, logger=None):
        self.__dbName = "wolf"
        self.__tableName = "wolf_runner"
        self.__db = None
        self.__logger = logger
        self.__database_schema = ("id INT AUTO_INCREMENT PRIMARY KEY, time TIMESTAMP, job VARCHAR(255), "
                                  "status INT, message VARCHAR(255)")
        self.working = self.__create_use_db()
        self.post_lock = threading.Lock()

    def __create_use_db(self):
        """
        Try to create the database with the name of the class variable dbName.
        If it already exists, use it.
        and set the cursor.

        :return: None
        """
        try:
            self.__db = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="root",
            )
        except mysql.connector.Error as e:
            self.__logger.error("Could not connect to database: " + str(e))
            return False
        self.__cursor = self.__db.cursor()
        try:  # Add if not exist
            self.__logger.warning("Creating database " + self.__dbName)
            self.__cursor.execute("CREATE DATABASE " + self.__dbName)
        except Exception as e:
            self.__logger.info("Could not create database: " + str(e))
        try:
            self.__db = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="root",
                database=self.__dbName
            )
        except mysql.connector.Error as e:
            self.__logger.error("Could not connect to database: " + str(e))
            return False
        self.__cursor = self.__db.cursor()
        try:  # Drop if exist
            self.__logger.warning("Dropping table " + self.__tableName)
            self.__cursor.execute("DROP TABLE " + self.__tableName)
        except Exception as e:
            self.__logger.info("Could not drop table: " + str(e))
        self.__cursor.execute(
            "CREATE TABLE " + self.__tableName + " (" + self.__database_schema + ")")
        return True

    def post(self, job, status, message):
        """
        Post a message to the database.

        :param job: The job name.
        :param status: The status of the job.
        :param message: The message of the job.
        :return: None
        """
        if self.working:
            sql = "INSERT INTO " + self.__tableName + " (time, job, status, message) VALUES (%s, %s, %s, %s)"
            val = (datetime.datetime.now(), job, status, message)
            self.post_lock.acquire()
            self.__cursor.execute(sql, val)
            self.__db.commit()
            self.post_lock.release()
