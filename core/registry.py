from django.core.exceptions import ImproperlyConfigured

from .exceptions import InstanceTypeDoesNotExist, InstanceTypeAlreadyRegistered


class Instance(object):
    """
    This abstract class represents a custom instance that can be added to the registry.
    It must be extended so properties and methods can be added.
    """

    type = None
    """A unique string that identifies the instance."""

    def __init__(self):
        if not self.type:
            raise ImproperlyConfigured("The type of an instance must be set.")


class ModelInstanceMixin:
    """
    This mixin introduces a model_class that will be related to the instance. It is to
    be used in combination with a registry that extends the ModelRegistryMixin.
    """

    model_class = None

    def __init__(self):
        if not self.model_class:
            raise ImproperlyConfigured("The model_class of an instance must be set.")


class ModelRegistryMixin:
    def get_by_model(self, model_instance):
        """
        Returns a registered instance of the given model class.

        :param model_instance: The value that must be or must be an instance of the
            model_class.
        :type model_instance: Model or Model()
        :raises InstanceTypeDoesNotExist: When the provided model instance is not
            found in the registry.
        :return: The registered instance.
        :rtype: Instance
        """

        most_specific_value = None
        for value in self.registry.values():
            value_model_class = value.model_class
            if value_model_class == model_instance or isinstance(
                    model_instance, value_model_class
            ):
                if most_specific_value is None:
                    most_specific_value = value
                else:
                    # There might be values where one is a sub type of another. The
                    # one with the longer mro is the more specific type (it inherits
                    # from more base classes)
                    most_specific_num_base_classes = len(
                        most_specific_value.model_class.mro()
                    )
                    value_num_base_classes = len(value_model_class.mro())
                    if value_num_base_classes > most_specific_num_base_classes:
                        most_specific_value = value

        if most_specific_value is not None:
            return most_specific_value

        raise self.does_not_exist_exception_class(
            f"The {self.name} model instance {model_instance} does not exist."
        )


class Registry(object):
    name = None
    """The unique name that is used when raising exceptions."""

    does_not_exist_exception_class = InstanceTypeDoesNotExist
    """The exception that is raised when an instance doesn't exist."""

    already_registered_exception_class = InstanceTypeAlreadyRegistered
    """The exception that is raised when an instance is already registered."""

    def __init__(self):
        if not self.name:
            raise ImproperlyConfigured(
                "The name must be set on an "
                "InstanceModelRegistry to raise proper errors."
            )

        self.registry = {}

    def get(self, type_name):
        """
        Returns a registered instance of the given type name.

        :param type_name: The unique name of the registered instance.
        :type type_name: str
        :raises InstanceTypeDoesNotExist: If the instance with the provided `type_name`
            does not exist in the registry.
        :return: The requested instance.
        :rtype: InstanceModelInstance
        """

        if type_name not in self.registry:
            raise self.does_not_exist_exception_class(
                type_name, f"The {self.name} type {type_name} does not exist."
            )

        return self.registry[type_name]

    def get_all(self):
        """
        Returns all registered instances

        :return: A list of the registered instances.
        :rtype: List[InstanceModelInstance]
        """

        return self.registry.values()

    def get_types(self):
        """
        Returns a list of available type names.

        :return: The list of available types.
        :rtype: List
        """

        return list(self.registry.keys())

    def get_types_as_tuples(self):
        """
        Returns a list of available type names.

        :return: The list of available types.
        :rtype: List[Tuple[str,str]]
        """

        return [(k, k) for k in self.registry.keys()]

    def register(self, instance):
        """
        Registers a new instance in the registry.

        :param instance: The instance that needs to be registered.
        :type instance: Instance
        :raises ValueError: When the provided instance is not an instance of Instance.
        :raises InstanceTypeAlreadyRegistered: When the instance's type has already
            been registered.
        """

        if not isinstance(instance, Instance):
            raise ValueError(f"The {self.name} must be an instance of " f"Instance.")

        if instance.type in self.registry:
            raise self.already_registered_exception_class(
                f"The {self.name} with type {instance.type} is already registered."
            )

        self.registry[instance.type] = instance

    def unregister(self, value):
        """
        Removes a registered instance from the registry. An instance or type name can be
        provided as value.

        :param value: The instance or type name.
        :type value: Instance or str
        :raises ValueError: If the provided value is not an instance of Instance or
            string containing the type name.
        """

        if isinstance(value, Instance):
            for type_name, instance in self.registry.items():
                if instance == value:
                    value = type_name

        if isinstance(value, str):
            del self.registry[value]
        else:
            raise ValueError(
                f"The value must either be an {self.name} instance or " f"type name"
            )


class APIUrlsRegistryMixin:
    @property
    def api_urls(self):
        """
        Returns a list of all the api urls that are in the registered instances.

        :return: The api urls of the registered instances.
        :rtype: list
        """

        api_urls = []
        for types in self.registry.values():
            api_urls += types.get_api_urls()
        return api_urls


class APIUrlsInstanceMixin:
    def get_api_urls(self):
        """
        If needed custom api related urls to the instance can be added here.

        Example:

            def get_api_urls(self):
                from . import api_urls

                return [
                    path('some-url/', include(api_urls, namespace=self.type)),
                ]

            # api_urls.py
            from django.urls import re_path

            urlpatterns = [
                url(r'some-view^$', SomeView.as_view(), name='some_view'),
            ]

        :return: A list containing the urls.
        :rtype: list
        """

        return []


class ImportExportMixin:
    def export_serialized(self, instance):
        """
        Should return with a serialized version of the provided instance. It must be
        JSON serializable and it must be possible to the import via the
        `import_serialized` method.

        :param instance: The instance that must be serialized and exported. Could be
            any object type because it depends on the type instance that uses this
            mixin.
        :type instance: Object
        :return: Serialized version of the instance.
        :rtype: dict
        """

        raise NotImplementedError("The export_serialized method must be implemented.")

    def import_serialized(self, parent, serialized_values, id_mapping):
        """
        Should import and create the correct instances in the database based on the
        serialized values exported by the `export_serialized` method. It should create
        a copy. An entry to the mapping could be made if a new instance is created.

        :param parent: Optionally a parent instance can be provided here.
        :type parent: Object
        :param serialized_values: The values that must be inserted.
        :type serialized_values: dict
        :param id_mapping: The map of exported ids to newly created ids that must be
            updated when a new instance has been created.
        :type id_mapping: dict
        :return: The newly created instance.
        :rtype: Object
        """

        raise NotImplementedError("The import_serialized method must be implemented.")
