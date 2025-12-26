import os
import importlib
import pkgutil

def register_handlers(bot):
    package_name = __name__  # bot.local
    package_path = os.path.dirname(__file__)
    parent_package_name = package_name.rpartition('.')[0]
    parent_package_path = os.path.dirname(package_path)

    private_modules = [
        importlib.import_module(f"{package_name}.{m.name}")
        for m in pkgutil.iter_modules([package_path])
        if not m.name.startswith("_")
    ]
    public_modules = [
        importlib.import_module(f"{parent_package_name}.{m.name}")
        for m in pkgutil.iter_modules([parent_package_path])
        if not m.name.startswith("_")
    ]

    for module in private_modules + public_modules:
        register_func = getattr(module, "register_handler", None)
        if callable(register_func):
            register_func(bot)