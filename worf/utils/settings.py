from contextlib import contextmanager
import importlib
import logging
import hashlib
import yaml
import json
import sys
import os

from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from collections import defaultdict, OrderedDict
from functools import wraps
import abc

from .settings_form import SettingsForm

logger = logging.getLogger(__name__)


class Worker(abc.ABC):
    @abc.abstractmethod
    def register(self, f):
        pass

    @abc.abstractmethod
    def run(self):
        pass


class CeleryWorker(Worker):
    def __init__(self, settings, config):
        from .celery import make_celery

        self.settings = settings
        self.config = config
        self.celery = make_celery(config)
        for task in self.settings.tasks:
            self.register(task)

    def register(self, task):
        self.celery.task(task)

    def run(self):
        argv = ["worker", "--loglevel=INFO", "-B"]
        self.celery.worker_main(argv)

    def delay(self, func, **kwargs):
        task_name = func.__module__ + "." + func.__name__
        return self.celery.send_task(task_name, kwargs=kwargs)


class ThreadWorker(Worker):
    def __init__(self, settings, config):
        self.settings = settings
        self.config = config

    def delay(self, func, **kwargs):
        return func(**kwargs)

    def register(self, f):
        pass

    def run(self):
        logger.info("Thread worker does not need to run explicitly...")


workers = {"thread": ThreadWorker, "celery": CeleryWorker}


class Settings:
    def __init__(self, d):
        self._d = d
        self.providers = defaultdict(list)
        self.hooks = defaultdict(list)
        self.sessionmaker = None
        self.initialized = False
        self.tasks = []
        self.worker = None

    def validate(self):
        self.form = SettingsForm(self._d)
        return self.form.validate()

    def register_task(self, task):
        self.tasks.append(task)
        if self.worker is not None:
            self.worker.register(task)
        return task

    def update(self, d):
        update(self._d, d)

    def setup_logging(self, level):
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
        level = levels[min(level, len(levels) - 1)]
        logging.basicConfig(level=level, format="%(message)s")

    def salted_hash(self, value):
        salt = self.get("salt", "")
        if salt == "":
            logger.warning("No salt value defined...")
        return hashlib.sha256(value.encode("utf-8") + salt.encode("utf-8")).hexdigest()

    def encrypt(self, data):
        key = self.get("encryption.key")
        f = Fernet(key)
        data_bytes = json.dumps(data).encode("utf-8")
        return f.encrypt(data_bytes)

    def decrypt(self, data, ttl=None):
        key = self.get("encryption.key")
        f = Fernet(key)
        data_bytes = f.decrypt(data, ttl=ttl)
        return json.loads(data_bytes.decode("utf-8"))

    def get_db_engine(self):
        """
        Returns a SQLAlchemy database engine.
        """
        params = self.get("db").copy()
        db_url = self.get("db.url").format(**params)
        engine = create_engine(db_url, echo=self.get("db.echo"))
        return engine

    @contextmanager
    def session(self, fresh=False, retry=False):
        session = self.get_session(fresh=fresh, retry=retry)
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self, fresh=False, retry=False):
        """
        Retrieves a session.
        """
        if fresh or self.sessionmaker is None:
            engine = self.get_db_engine()
            if self.sessionmaker is not None:
                self.dispose_all_sessions()
            self.sessionmaker = scoped_session(
                sessionmaker(bind=engine, expire_on_commit=False)
            )
        return self.sessionmaker()

    def dispose_all_sessions(self):
        """
        Disposes all open sessions.
        """
        if self.sessionmaker is None:
            return
        self.sessionmaker.close_all()
        self.sessionmaker.get_bind().dispose()
        self.sessionmaker = None

    def initialize(self):
        logger.debug("Initializing settings...")
        self.load_plugins()
        self.initialize_worker()

    def initialize_worker(self):
        worker_type = self.get("worker.type")
        self.worker = workers[worker_type](self, self.get("worker"))

    def delay(self, func, **kwargs):
        self.worker.delay(func, **kwargs)

    def get(self, key, default=None):
        """
        Get a settings value
        """
        components = key.split(".")

        cd = self._d
        for component in components:
            if component in cd:
                cd = cd[component]
            else:
                return default
        return cd

    def set(self, key, value):
        """
        Set a settings value
        """
        components = key.split(".")
        cd = self._d
        for component in components[:-1]:
            if not component in cd:
                cd[component] = {}
            cd = cd[component]
        if value is None:
            del cd[components[-1]]
        else:
            cd[components[-1]] = value

    def load_plugin_module(self, name):
        plugin_data = self.get("plugins.{}".format(name))
        if plugin_data is None:
            raise ValueError("Unknown plugin: {}".format(name))

        setup_module_name = "{}.setup".format(plugin_data["module"])
        setup_module = importlib.import_module(setup_module_name)
        return setup_module

    def load_plugin_config(self, name, setup_module=None):
        if setup_module is None:
            setup_module = self.load_plugin_module(name)
        return setup_module.config

    def get_plugin_path(self, name):
        setup_module = self.load_plugin_module(name)
        return os.path.dirname(setup_module.__file__)

    def load_plugin(self, name):
        """Loads the plugin with the given name
        :param name: name of the plugin to load
        """

        plugin_data = self.get("plugins.{}".format(name))
        if plugin_data is None:
            raise ValueError("Unknown plugin: {}".format(name))

        logger.debug("Loading plugin: {}".format(name))
        config = self.load_plugin_config(name)

        # register providers
        for name, params in config.get("providers", {}).items():
            self.providers[name].append(params)

        # register hooks
        for name, params in config.get("hooks", {}).items():
            self.hooks[name].append(params)

        # register task schedule
        schedule = self.get("worker.schedule", {})
        schedule.update(plugin_data.get("schedule", {}))
        self.set("worker.schedule", schedule)

        for filename in config.get("yaml_settings", []):
            with open(filename) as yaml_file:
                settings_yaml = yaml.load(yaml_file.read(), Loader=yaml.FullLoader)
                update(self._d, settings_yaml, overwrite=False)

    def order_plugins(self):
        plugins = self.get("plugins") or {}
        ordered_plugins = OrderedDict()
        dependents = defaultdict(list)
        for name, plugin_settings in plugins.items():
            dependencies = plugin_settings.get("depends_on", [])
            # we check whether this plugin has any dependencies. If it does,
            # we make sure all dependencies are loaded before loading it
            if dependencies:
                delay = False
                for dependency in dependencies:
                    if dependency not in ordered_plugins:
                        if dependency not in plugins:
                            raise ValueError(
                                f"plugin {name} requires {dependency}, but is not loaded"
                            )
                        dependents[dependency].append(name)
                        delay = True
                        break
                if delay:
                    continue
            ordered_plugins[name] = plugin_settings
            # we check for dependent plugins and ad dthem
            if name in dependents:
                for dependent_plugins in dependents.values():
                    for dependent in dependent_plugins:
                        ordered_plugins[dependent] = plugins[dependent]
                del dependents[name]
        if dependents:
            logger.error("Remaining dependents:", dict(dependents))
            raise ValueError(
                "not all dependencies were resolved, possibly there is a circular dependency"
            )
        return ordered_plugins

    def load_plugins(self):
        """Loads all plugins specified in settings if they have not yet been loaded."""
        ordered_plugins = self.order_plugins()
        for name in ordered_plugins:
            self.load_plugin(name)

    def get_plugin_apis(self):
        """Generator over all routes provided by all plugins
        :return: API dictionary with version, routes and module name
        """
        apis = {}
        for plugin_name in self.get("plugins", {}):
            config = self.load_plugin_config(plugin_name)
            endpoint_config = config.get("api")
            if endpoint_config:
                apis[plugin_name] = endpoint_config
        return apis

    def get_plugin_exports(self, resource_name):
        """Returns a combined export map for the given resource from all plugins.
        :param resource: resource name
        :return: combined export map for the given resource
        """
        exports = tuple()
        for plugin_name in self.get("plugins", {}):
            config = self.load_plugin_config(plugin_name)
            exports += config.get("exports", {}).get(resource_name, ())
        return list(exports)

    def get_plugin_includes(self, resource_name):
        """Returns a list of all `includes` for the given resource from all
        plugins as a dictionary with HTTP methods
        as keys and a list of additional includes as the value.
        Example: the GitHub plugin adds a `github` parameter to the user object,
        which needs to be provided in the include
        argument of a database get call to be returned

        :param resource: resource name
        :return: dictionary of HTTP method: list of includes

        """
        includes = set()
        for plugin_name in self.get("plugins", {}):
            config = self.load_plugin_config(plugin_name)
            includes_config = config.get("includes")
            if includes_config:
                includes |= set(includes_config.get(resource_name, ()))
        return list(includes)

    @property
    def translations(self):
        return self.get("translations", {})

    def translate(self, language, key, *args, **kwargs):
        translation = self.get("translations.{}.{}".format(key, language))
        if not translation:
            return "[no translation for language {} and key {}]".format(language, key)
        return translation.format(*args, **kwargs)


def get_func_by_name(name):
    components = name.split(".")
    module_name, func_name = ".".join(components[:-1]), components[-1]
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


def load_settings(filenames):
    settings_dict = {}
    for filename in filenames:
        with open(filename, "r") as yaml_file:
            settings_yaml = yaml.load(yaml_file.read(), Loader=yaml.FullLoader)
            if settings_yaml is None:
                continue
            c = {"cwd": os.path.dirname(os.path.abspath(filename))}
            interpolate(settings_yaml, c)
            update(settings_dict, settings_yaml)
    return settings_dict


def update(d, ud, overwrite=True):
    for key, value in ud.items():
        if key not in d:
            d[key] = value
        elif isinstance(value, dict) and isinstance(d[key], dict):
            update(d[key], value, overwrite=overwrite)
        else:
            if key in d and not overwrite:
                continue
            d[key] = value


def interpolate(d, context):
    def format(s):
        try:
            return s.format(**context)
        except KeyError:
            return s

    if isinstance(d, dict):
        for key, value in d.items():
            if isinstance(value, str):
                d[key] = format(value)
            elif isinstance(value, dict):
                interpolate(value, context)
            elif isinstance(value, list):
                interpolate(value, context)
    elif isinstance(d, list):
        for i, value in enumerate(d):
            if isinstance(value, str):
                d[i] = format(value)
            else:
                interpolate(value, context)
