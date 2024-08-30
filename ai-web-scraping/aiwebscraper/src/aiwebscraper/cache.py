import inspect
import json
import logging
import sqlite3
from pathlib import Path


logger = logging.getLogger(__name__)


class CachedException(Exception):
    pass


class FunctionCache:
    """
    Adds SQLite caching to a function so we don't have to call the function every time.
    The cache key are all the function's name, the source code, and the keyword arguments
    passed to the function. The function must return a JSON-serializable object.

    Parameters
    ----------
    function : callable
        The function to cache. Must only accept keyword arguments.

    path_to_db : str
        Path to the SQLite database file. If the file does not exist, it will be
        created.
    """

    def __init__(self, function, path_to_db, retry_failures=False) -> None:
        self._path_to_db = path_to_db
        self._connection = None
        self._function = function
        self._qualified_name = self.qualified_name(function)
        self._source_code = inspect.getsource(function)
        self._retry_failures = retry_failures

        self.validate_function(function)

        if not Path(self._path_to_db).exists():
            self._create_db()

    def clear_cache(self):
        """Clear the cache by deleting the SQLite database file."""
        if self._connection is not None:
            self._connection.close()

        Path(self._path_to_db).unlink()
        self._create_db()

    def validate_function(self, function):
        """Validate that the function only has keyword arguments and no default
        arguments."""
        signature = inspect.signature(function)

        for parameter in signature.parameters.values():
            if (
                parameter.default is not inspect.Parameter.empty
                or parameter.kind != inspect.Parameter.KEYWORD_ONLY
            ):
                raise ValueError(
                    f"The function {self._qualified_name} must only have keyword arguments and no default arguments."
                )

    @staticmethod
    def qualified_name(function):
        """Return the fully qualified name of a function."""
        return function.__module__ + "." + function.__qualname__

    @property
    def connection(self):
        """Return the SQLite connection. If it doesn't exist, create it."""
        if self._connection is None:
            self._connection = sqlite3.connect(self._path_to_db)

        return self._connection

    def __del__(self):
        """Close the connection when the object is deleted."""
        if self._connection is not None:
            self._connection.close()

    def _create_db(self):
        """Create the SQLite database and the table to store the function calls."""
        Path(self._path_to_db).parent.mkdir(parents=True, exist_ok=True)
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS calls (
                qualified_name TEXT,
                kwargs TEXT,
                source_code TEXT,
                response TEXT,
                exception TEXT
            )
        """
        )

        self.connection.commit()

    def _insert(self, *, kwargs: dict, response: dict, exception: str):
        """Insert a new function call into the database."""
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO calls (qualified_name, kwargs, source_code, response, exception)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                self._qualified_name,
                json.dumps(kwargs),
                self._source_code,
                json.dumps(response),
                exception,
            ),
        )

        self.connection.commit()

    def _lookup(self, *, kwargs: dict):
        """Look up a function call in the database by matching the qualified name and
        kwargs. Return None if not found.

        Parameters
        ----------
        kwargs : dict
            The keyword arguments passed to the function.

        Returns
        -------
        dict
            The response from the function if found, otherwise None.
        """
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT response, exception
            FROM calls
            WHERE qualified_name = ? AND kwargs = ? AND source_code = ?
        """,
            (self._qualified_name, json.dumps(kwargs), self._source_code),
        )

        result = cursor.fetchone()

        # no cache hit
        if result is None:
            logger.info(f"Cache miss, calling {self._qualified_name}")
            return None

        response, exception = result

        if exception is not None:
            # no cache hit
            if self._retry_failures:
                logger.info(
                    "Cache miss (function raised an exception and "
                    f"retry_failures is True), calling {self._qualified_name}"
                )
                return None
            else:
                raise CachedException(exception)

        return json.loads(response)

    def __call__(self, **kwargs):
        """Call the function, caching the result if it's not already in the database.
        kwargs must be JSON-serializable."""
        response = self._lookup(kwargs=kwargs)

        if response is None:
            try:
                response = self._function(**kwargs)
            except Exception as e:
                response = None
                exception = f"{e.__class__.__name__}: {str(e)}"
                exception_instance = e
            else:
                exception = None
                exception_instance = None

            self._insert(
                kwargs=kwargs,
                response=response,
                exception=exception,
            )

            if exception_instance is not None:
                raise exception_instance

        return response
