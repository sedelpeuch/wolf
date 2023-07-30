#! /usr/bin/env python3

"""
This module contains the API interface.
"""
import logging
from abc import ABC

import jsonschema


def type_check(*type_args, **type_kwargs) -> callable:
    """
    Decorator that checks the types of the arguments passed to a function.

    :param type_args: Positional arguments represent the types of the function arguments.
    :param type_kwargs: Keyword arguments representing the types of the function keyword arguments.
    :return: Decorator function that performs the type checking.
    """

    def decorator(func) -> callable:
        """
        This decorator ensures that the arguments passed to the decorated function match the specified types.

        The decorator takes a function as an input and returns a wrapped function.
        The wrapped function performs argument type checking before calling the original function.
        If the argument types do not match the specified types, a TypeError is raised with an appropriate error message.

        The decorator supports both positional arguments and keyword arguments.
        It checks the types of positional arguments based on their order and the types of
        keyword arguments based on their names.

        Note: The decorator assumes that the specified types are imported and available in the decorator's scope.

        :param func: The function to be decorated.
        :return: The decorated function.
        """

        def wrapper(*args, **kwargs) -> callable:
            """
            Wrap the given function with type checking for positional arguments and keyword arguments.

            :param args: Positional arguments to be passed to the function.
            :param kwargs: Keyword arguments to be passed to the function.

            :return: The return value of the function.

            :raises TypeError: If there are too many or too few positional arguments,
                                or if any argument or keyword argument does not match its expected type.
            """
            args_list = list(args)
            if isinstance(type_args[0], list):
                type_args_list = type_args[0]
            else:
                type_args_list = type_args
            if len(args_list) > len(type_args_list):
                raise TypeError('Too many positional arguments')

            for i, (arg, type_arg) in enumerate(zip(args_list, type_args_list)):
                if not isinstance(arg, type_arg):
                    raise TypeError('Argument {} must be {}'.format(i, type_arg))

            for key, type_value in type_kwargs.items():
                try:
                    value = kwargs[key]
                except KeyError:
                    continue
                if not isinstance(value, type_value):
                    raise TypeError(f'Argument {key} must be {type_value}')

            return func(*args, **kwargs)

        return wrapper

    return decorator


class API(ABC):
    """
    This class is the main class of the core module.

    :param url: The main url for the API.
    :type url: str
    :param test_url: The test url for the API.
    :type test_url: str
    :param token: The token used for authentication.
    :type token: str
    :param test: Optional flag to indicate whether to use the test url or the main url. Defaults to False.
    :type test: bool, optional
    :param ressources: The dictionary of resources and their corresponding methods and parameters.Ressources must
    follow the following schema:
        {
            "ressource_name": {
                "verb": "GET" | "POST" | "PUT" | "DELETE",
                "method": method_name,
                "params": [str, int, float, list, dict, bool, None]
            }
        }
    :type ressources: dict

    """

    instances = []

    def __init__(self, url=None, test_url=None, token=None, test=False, ressources=None):
        self._url = test_url if test else url
        self._token = token
        self.__class__.instances.append(self)
        self.logger = logging.getLogger(__name__)

        # Create the get, post, put and delete classes to store methods
        # Allow to use self.get.method_name() instead of self.get_method_name()
        # Perform type checking and validation schema
        self.get = type("get", (), {})
        self.post = type("post", (), {})
        self.put = type("put", (), {})
        self.delete = type("delete", (), {})
        self.patch = type("patch", (), {})

        self.ressources_schema = {
            "verb": {"enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
            "method": {"type": "function"},
            "params": {"enum": [str, int, float, list, dict, bool, None]},
            "optional_params": {"enum": [str, int, float, list, dict, bool, None]}
        }
        self.ressources = ressources
        for ressource in self.ressources:
            try:
                jsonschema.validate(self.ressources[ressource], self.ressources_schema)
            except jsonschema.exceptions.ValidationError as e:
                self.logger.error(f"Invalid ressource {ressource}: {e.message}")
        self.set_method()

    def type_wrap(self, ressource) -> type:
        """
        Wrapper method for HTTP methods based on the verb associated with the given resource.

        :param ressource: The resource for which the HTTP method is being wrapped.
        :type ressource: dict
        :return: The wrapped HTTP method.
        :raises ValueError: If the verb associated with the resource is invalid.
        """
        http_methods = {
            'GET': self.get,
            'POST': self.post,
            'PUT': self.put,
            'PATCH': self.patch,
            'DELETE': self.delete
        }

        verb = ressource["verb"]
        type_wrap = http_methods.get(verb)

        if type_wrap is None:
            raise ValueError(f"Invalid verb: {verb}")
        return type_wrap

    def set_method(self):
        """
        Process the resources and sub-resources.

        :return: None
        """
        for resource, resource_value in self.ressources.items():
            if "verb" in resource_value.keys():
                self.process_resource(resource, resource_value)
            else:
                self.process_sub_resource(resource, resource_value)

    @staticmethod
    def get_parameters(resource):
        """
        Get the parameters for the specified resource.

        :param resource: A dictionary representing the resource for which the parameters need to be retrieved.
        :return: A list of parameters for the specified resource.
        """
        params = resource["params"]
        optional_params = resource["optional_params"] if "optional_params" in resource else None
        contact = []
        if params is not None:
            if isinstance(params, list):
                contact += params
            else:
                contact.append(params)
        if optional_params is not None:
            if isinstance(optional_params, list):
                contact += optional_params
            else:
                contact.append(optional_params)
        return contact

    def process_resource(self, resource, resource_value):
        """
        Process a resource.

        :param resource: The resource name.
        :param resource_value: The value of the resource.
        :return: None.
        """
        try:
            method = resource_value["method"]
        except KeyError:
            raise ValueError(f"Invalid resource: {resource}")

        type_wrap = self.type_wrap(resource_value)
        parameters = self.get_parameters(resource_value)

        setattr(type_wrap, resource, method)
        setattr(type_wrap, resource,
                type_check(parameters)(getattr(type_wrap, resource)))

    def process_sub_resource(self, super_resource_name, super_resource):
        """
        This method processes the sub-resource by iterating over the items of the super_resource dictionary.
        For each item, it retrieves the "method" value and performs error handling in case it is missing.

        The method then calls the type_wrap method to wrap the resource value
        and obtains the parameters using the get_parameters method.

        Finally, it sets the super_resource_name attribute of the type_wrap object to the method value.
        It also applies type checking using the type_check decorator to the method attribute.

        :param super_resource_name: The name of the sub-resource being processed.
        :param super_resource: A dictionary containing the super resource and its values.
        :return: None
        """
        for resource, resource_value in super_resource.items():
            try:
                method = resource_value["method"]
            except KeyError:
                raise ValueError(f"Invalid resource: {resource}")

            type_wrap = self.type_wrap(resource_value)
            parameters = self.get_parameters(resource_value)

            setattr(type_wrap, super_resource_name, method)
            setattr(type_wrap, super_resource_name, type_check(parameters)(getattr(type_wrap, super_resource_name)))


class RequestResponse:
    """
    This class is used to store the response from an API request.

    :param status_code: The status code of the response.
    :type status_code: int
    :param data: The data in the response.
    :type data: dict
    """

    def __init__(self, status_code, data):
        """
        This is the constructor of the class.
        """
        if not isinstance(status_code, int):
            raise TypeError("`status_code` must be an integer")
        if not isinstance(data, dict):
            raise TypeError("`data` must be a dictionary")
        self._status_code = status_code
        self._data = data

    @property
    def status_code(self):
        """
        This is the status code property.
        """
        return self._status_code

    @property
    def data(self):
        """
        This is the data property.
        """
        return self._data

    def __eq__(self, other):
        if not isinstance(other, RequestResponse):
            return False
        return self.status_code == other.status_code and self.data == other.data
