from constance.backends import Backend as BaseConstanceBackend


class ConstanceDictBackend(BaseConstanceBackend):
    """A simple dict-based constance backend for testing purposes."""

    def __init__(self):
        self.storage = {}

    def get(self, key):
        """
        Get the key from the backend store and return the value.
        Return None if not found.
        """
        return self.storage.get(key)

    def mget(self, keys):
        """
        Get the keys from the backend store and return a list of the values.
        Return an empty list if not found.
        """
        return [self.storage[k] for k in keys if k in self.storage]

    def set(self, key, value):
        """
        Add the value to the backend store given the key.
        """
        self.storage[key] = value
