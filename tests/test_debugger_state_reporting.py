import ast
import sys
from pathlib import Path
from types import SimpleNamespace


SOURCE = Path("packages/debugger-mcp/debugger_mcp.py")


def _load_functions(modules, active_window=object()):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    wanted = {
        "get_debugger",
        "_get_all_sessions",
        "_get_adapters",
        "_get_breakpoints",
        "_debugger_command_args",
    }
    selected = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in wanted
    ]
    namespace = {
        "sys": SimpleNamespace(modules=modules),
        "sublime": SimpleNamespace(active_window=lambda: active_window),
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace


def test_all_sessions_reports_package_missing():
    get_all_sessions = _load_functions({})["_get_all_sessions"]

    assert get_all_sessions() == {"error": "Debugger package not loaded."}


def test_all_sessions_distinguishes_loaded_but_inactive():
    class Debugger:
        debuggers_for_window = {}

        @staticmethod
        def get(window, create=False):
            return None

    modules = {"Debugger.modules.debugger": SimpleNamespace(Debugger=Debugger)}
    get_all_sessions = _load_functions(modules)["_get_all_sessions"]

    assert get_all_sessions() == {
        "sessions": [],
        "status": "inactive",
        "message": "Debugger is loaded, but not active in any Sublime window.",
    }


def test_all_sessions_reports_active_sessions():
    session = SimpleNamespace(name="Python", state="paused")
    instance = SimpleNamespace(
        sessions=[session],
        is_running=lambda: True,
        is_open=lambda: True,
    )

    class Debugger:
        debuggers_for_window = {1: instance}

        @staticmethod
        def get(window, create=False):
            return instance

    modules = {"Debugger.modules.debugger": SimpleNamespace(Debugger=Debugger)}
    get_all_sessions = _load_functions(modules)["_get_all_sessions"]

    assert get_all_sessions() == {
        "sessions": [{"name": "Python", "state": "paused"}],
        "status": "active",
    }


def test_get_adapters_uses_current_debugger_registry():
    registry = SimpleNamespace(registered=[
        SimpleNamespace(type="gdb"),
        SimpleNamespace(type=["debugpy", "python"]),
        SimpleNamespace(type="gdb"),
    ])
    modules = {
        "Debugger.modules.dap": SimpleNamespace(AdapterConfiguration=registry)
    }
    get_adapters = _load_functions(modules)["_get_adapters"]

    assert get_adapters() == {
        "adapters": [
            {"name": "debugpy"},
            {"name": "gdb"},
            {"name": "python"},
        ]
    }


def test_get_breakpoints_reports_package_missing():
    get_breakpoints = _load_functions({})["_get_breakpoints"]

    assert get_breakpoints() == {"error": "Debugger package not loaded."}


def test_get_breakpoints_distinguishes_loaded_but_inactive():
    class Debugger:
        debuggers_for_window = {}

        @staticmethod
        def get(window, create=False):
            return None

    modules = {"Debugger.modules.debugger": SimpleNamespace(Debugger=Debugger)}
    get_breakpoints = _load_functions(modules)["_get_breakpoints"]

    assert get_breakpoints() == {
        "source_breakpoints": [],
        "function_breakpoints": [],
        "status": "inactive",
        "message": "Debugger is loaded, but not active in any Sublime window.",
    }


def test_get_breakpoints_reports_active_breakpoints():
    source = SimpleNamespace(
        breakpoints=[SimpleNamespace(
            file="example.py",
            line=7,
            enabled=True,
            dap=SimpleNamespace(condition=None, logMessage=None),
        )]
    )
    function = SimpleNamespace(
        breakpoints=[SimpleNamespace(name="main", enabled=True, dap=SimpleNamespace(condition="x"))]
    )
    instance = SimpleNamespace(
        breakpoints=SimpleNamespace(source=source, function=function),
        is_running=lambda: False,
        is_open=lambda: True,
    )

    class Debugger:
        debuggers_for_window = {1: instance}

        @staticmethod
        def get(window, create=False):
            return instance

    modules = {"Debugger.modules.debugger": SimpleNamespace(Debugger=Debugger)}
    get_breakpoints = _load_functions(modules)["_get_breakpoints"]

    assert get_breakpoints() == {
        "source_breakpoints": [{
            "file": "example.py",
            "line": 7,
            "enabled": True,
            "condition": None,
            "log_message": None,
        }],
        "function_breakpoints": [{
            "name": "main",
            "enabled": True,
            "condition": "x",
        }],
        "status": "active",
    }


def test_start_maps_configuration_name_to_debugger_configuration_argument():
    command_args = _load_functions({})["_debugger_command_args"]

    assert command_args("start", {"configuration_name": "Python"}) == {
        "configuration": "Python"
    }
    assert command_args("open_and_start", {"configuration_name": "Python"}) == {
        "configuration": "Python"
    }


def test_other_commands_preserve_configuration_name_argument():
    command_args = _load_functions({})["_debugger_command_args"]

    assert command_args("change_configuration", {"configuration_name": "Python"}) == {
        "configuration_name": "Python"
    }
    assert command_args("start", {}) == {}


def test_http_log_message_overrides_match_base_parameter_name():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    overrides = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "log_message"
    ]

    assert len(overrides) == 2
    assert all(node.args.args[1].arg == "format" for node in overrides)
