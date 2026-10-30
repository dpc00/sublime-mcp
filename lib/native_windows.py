"""List and dismiss the native OS windows (dialogs, menus) of one process (Windows only).

A Sublime Text command that opens a native dialog or menu (``prompt_open_file``,
``delete_file``, ``context_menu``, ...) blocks Sublime's main thread until a person
dismisses it, so every MCP tool that goes through the main thread times out. The
functions here need no main thread and no ``sublime`` module: they use Win32 calls
on the windows of a given process id, so an HTTP request thread can still see and
dismiss the window while Sublime is blocked.

Every entry point checks the window's process id first, so only windows of the
given process are ever acted on.
"""

import sys
import time

WM_CLOSE = 0x0010
BM_CLICK = 0x00F5
IDOK = 1
IDCANCEL = 2
BS_TYPEMASK = 0x0F
BS_DEFPUSHBUTTON = 0x01
GWL_STYLE = -16

CANCEL_TEXTS = ("cancel", "no", "close", "abort", "don't save", "dont save")
OK_TEXTS = ("ok", "yes", "open", "save", "select folder", "delete", "remove", "continue", "retry")

SUPPORTED = sys.platform == "win32"

if SUPPORTED:
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
    _user32.EnumChildWindows.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.LPARAM]
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    _user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.IsWindowVisible.argtypes = [wintypes.HWND]
    _user32.IsWindowEnabled.argtypes = [wintypes.HWND]
    _user32.IsWindow.argtypes = [wintypes.HWND]
    _user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _user32.GetDlgCtrlID.argtypes = [wintypes.HWND]
    _user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    _ENUM_PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


if SUPPORTED:
    _kernel32 = ctypes.windll.kernel32
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def image_name(pid):
    """Lower-case executable file name of process ``pid`` ("" when unknown)."""
    if not SUPPORTED:
        return ""
    handle = _kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(1024)
        if not _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return ""
        return buf.value.replace("/", "\\").rsplit("\\", 1)[-1].lower()
    finally:
        _kernel32.CloseHandle(handle)


def sublime_pid(own_pid, parent_pid):
    """The pid that owns Sublime Text's windows. Plugins run in a separate plugin-host
    process, so the windows belong to its parent: return whichever of the two is
    sublime_text.exe, falling back to the parent."""
    for pid in (parent_pid, own_pid):
        if image_name(pid) == "sublime_text.exe":
            return pid
    return parent_pid


def classify(class_name, title):
    """Return "dialog", "menu", "editor_window", "window" or "other" for a window."""
    if class_name == "#32770":
        return "dialog"
    if class_name == "#32768":
        return "menu"
    if class_name == "PX_WINDOW_CLASS":
        return "editor_window" if " - Sublime Text" in (title or "") else "window"
    return "other"


def _strip_mnemonic(text):
    return (text or "").replace("&", "").strip()


def pick_button(buttons, action, button_text=None):
    """Choose the button an action means. ``buttons`` is a list of dicts with
    ``id``, ``text`` and ``default``. Returns the chosen dict or None.

    action "button" needs ``button_text`` and matches it ignoring case and
    mnemonic ampersands; "cancel" prefers IDCANCEL then a cancel-like label;
    "ok" prefers IDOK, then an ok-like label, then the default button."""
    def norm(b):
        return _strip_mnemonic(b.get("text")).lower()

    if action == "button":
        want = _strip_mnemonic(button_text).lower()
        for b in buttons:
            if norm(b) == want:
                return b
        return None
    if action == "cancel":
        for b in buttons:
            if b.get("id") == IDCANCEL:
                return b
        for b in buttons:
            if norm(b) in CANCEL_TEXTS:
                return b
        return None
    if action == "ok":
        for b in buttons:
            if b.get("id") == IDOK:
                return b
        for b in buttons:
            if norm(b) in OK_TEXTS:
                return b
        for b in buttons:
            if b.get("default"):
                return b
        return None
    return None


if SUPPORTED:
    def _text(hwnd):
        n = _user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 2)
        _user32.GetWindowTextW(hwnd, buf, n + 2)
        return buf.value

    def _class(hwnd):
        buf = ctypes.create_unicode_buffer(256)
        _user32.GetClassNameW(hwnd, buf, 256)
        return buf.value

    def _pid(hwnd):
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value

    def _children(hwnd):
        out = []

        def cb(child, _):
            out.append(child)
            return True

        proc = _ENUM_PROC(cb)
        _user32.EnumChildWindows(hwnd, proc, 0)
        return out

    # UI Automation fallback. A Windows task dialog (custom button text, such as "Install" /
    # "Cancel") draws its message without child windows of class "Static", so the walk in
    # _dialog_parts finds no text. UI Automation reads it. Plain ctypes on the COM vtables
    # (no comtypes, no helper process); indexes checked against UIAutomationClient.idl
    # (Windows SDK 10.0.18362).
    _UIA_TEXT_CONTROL_TYPE = 50020
    _UIA_CONTROL_TYPE_PROPERTY = 30003
    _UIA_NAME_PROPERTY = 30005
    _TREE_SCOPE_DESCENDANTS = 4
    _VT_I4 = 3
    _VT_BSTR = 8

    class _GUID(ctypes.Structure):
        _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                    ("Data4", ctypes.c_ubyte * 8)]

    class _VARIANT(ctypes.Structure):
        _fields_ = [("vt", ctypes.c_ushort), ("r1", ctypes.c_ushort), ("r2", ctypes.c_ushort),
                    ("r3", ctypes.c_ushort), ("val", ctypes.c_void_p), ("val2", ctypes.c_void_p)]

    def _guid(text):
        g = _GUID()
        ctypes.oledll.ole32.CLSIDFromString(text, ctypes.byref(g))
        return g

    def _vcall(obj, index, *argtypes):
        """The COM method at vtable ``index`` of interface pointer ``obj``, as a callable that
        takes the arguments after ``this`` and returns the HRESULT."""
        ptr = ctypes.cast(obj, ctypes.POINTER(ctypes.c_void_p))
        vtbl = ctypes.cast(ptr[0], ctypes.POINTER(ctypes.c_void_p))
        proto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argtypes)
        fn = proto(vtbl[index])
        return lambda *args: fn(obj, *args)

    def _release(obj):
        if obj and obj.value:
            _vcall(obj, 2)()

    def _uia_texts(hwnd):
        """Names of the Text elements under window ``hwnd``, in tree order, empty ones skipped.
        Returns [] when UI Automation is not available or the window cannot be read."""
        ole32 = ctypes.windll.ole32
        oleaut32 = ctypes.windll.oleaut32
        hr_init = ole32.CoInitializeEx(None, 0)  # multithreaded: no message pump needed
        owned, texts = [], []
        try:
            auto = ctypes.c_void_p()
            hr = ole32.CoCreateInstance(ctypes.byref(_guid("{ff48dba4-60ef-4201-aa87-54103eef594e}")),
                                        None, 1 | 4,  # CLSCTX_INPROC_SERVER | CLSCTX_LOCAL_SERVER
                                        ctypes.byref(_guid("{30cbe57d-d9d0-452a-ab13-7ac5ac4825ee}")),
                                        ctypes.byref(auto))
            if hr != 0 or not auto.value:
                return []
            owned.append(auto)
            root = ctypes.c_void_p()
            if _vcall(auto, 6, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))(hwnd, ctypes.byref(root)) != 0:
                return []
            owned.append(root)
            cond = ctypes.c_void_p()
            if _vcall(auto, 21, ctypes.POINTER(ctypes.c_void_p))(ctypes.byref(cond)) != 0:
                return []
            owned.append(cond)
            found = ctypes.c_void_p()
            if _vcall(root, 6, ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))(
                    _TREE_SCOPE_DESCENDANTS, cond, ctypes.byref(found)) != 0:
                return []
            owned.append(found)
            count = ctypes.c_int()
            _vcall(found, 3, ctypes.POINTER(ctypes.c_int))(ctypes.byref(count))
            for i in range(min(count.value, 200)):
                el = ctypes.c_void_p()
                if _vcall(found, 4, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))(i, ctypes.byref(el)) != 0:
                    continue
                try:
                    kind = _VARIANT()
                    get_prop = _vcall(el, 10, ctypes.c_int, ctypes.POINTER(_VARIANT))
                    if get_prop(_UIA_CONTROL_TYPE_PROPERTY, ctypes.byref(kind)) != 0:
                        continue
                    is_text = kind.vt == _VT_I4 and (kind.val or 0) & 0xFFFFFFFF == _UIA_TEXT_CONTROL_TYPE
                    oleaut32.VariantClear(ctypes.byref(kind))
                    if not is_text:
                        continue
                    name = _VARIANT()
                    if get_prop(_UIA_NAME_PROPERTY, ctypes.byref(name)) == 0:
                        if name.vt == _VT_BSTR and name.val:
                            t = ctypes.wstring_at(name.val).strip()
                            if t:
                                texts.append(t)
                        oleaut32.VariantClear(ctypes.byref(name))
                finally:
                    _release(el)
        except Exception:
            return texts
        finally:
            for obj in reversed(owned):
                _release(obj)
            if hr_init in (0, 1):
                ole32.CoUninitialize()
        return texts

    def _dialog_parts(hwnd):
        buttons, messages = [], []
        for child in _children(hwnd):
            cls = _class(child)
            if cls == "Button":
                style = _user32.GetWindowLongW(child, GWL_STYLE)
                buttons.append({
                    "hwnd": int(child),
                    "id": _user32.GetDlgCtrlID(child),
                    "text": _strip_mnemonic(_text(child)),
                    "default": (style & BS_TYPEMASK) == BS_DEFPUSHBUTTON,
                })
            elif cls == "Static":
                t = _text(child).strip()
                if t:
                    messages.append(t)
        if not messages:
            messages = _uia_texts(hwnd)
        return buttons, messages[:4]


def list_windows(pid):
    """Visible top-level windows of process ``pid`` with class, title, kind and,
    for dialogs, their buttons and message text."""
    if not SUPPORTED:
        raise NotImplementedError("native window handling is implemented for Windows only")
    found = []

    def cb(hwnd, _):
        if _pid(hwnd) == pid and _user32.IsWindowVisible(hwnd):
            cls, title = _class(hwnd), _text(hwnd)
            rect = wintypes.RECT()
            _user32.GetWindowRect(hwnd, ctypes.byref(rect))
            entry = {
                "hwnd": int(hwnd),
                "class": cls,
                "title": title,
                "kind": classify(cls, title),
                "enabled": bool(_user32.IsWindowEnabled(hwnd)),
                "rect": [rect.left, rect.top, rect.right, rect.bottom],
            }
            if entry["kind"] == "dialog":
                entry["buttons"], entry["messages"] = _dialog_parts(hwnd)
            found.append(entry)
        return True

    proc = _ENUM_PROC(cb)
    _user32.EnumWindows(proc, 0)
    return found


def dismiss(pid, hwnd=None, action="cancel", button_text=None, wait=2.0):
    """Dismiss a dialog or menu of process ``pid``.

    hwnd: the window to act on; default is the first dialog, then the first menu.
    action: "cancel" (default), "ok", "close" (WM_CLOSE) or "button" (with button_text).
    Returns a dict with ``ok``, ``closed`` (window gone after up to ``wait`` seconds)
    and what was done. Never raises for an unsuitable window; it reports instead."""
    if not SUPPORTED:
        raise NotImplementedError("native window handling is implemented for Windows only")
    if action not in ("cancel", "ok", "close", "button"):
        return {"ok": False, "error": "action must be cancel, ok, close or button"}
    if action == "button" and not button_text:
        return {"ok": False, "error": "action 'button' needs button_text"}
    windows = list_windows(pid)
    target = None
    if hwnd is not None:
        target = next((w for w in windows if w["hwnd"] == int(hwnd)), None)
        if target is None:
            return {"ok": False, "error": "hwnd {} is not a visible window of this Sublime Text process".format(hwnd)}
    else:
        for kind in ("dialog", "menu"):
            target = next((w for w in windows if w["kind"] == kind), None)
            if target:
                break
        if target is None:
            return {"ok": False, "error": "no native dialog or menu is open", "windows": len(windows)}

    done = None
    if target["kind"] == "dialog" and action != "close":
        chosen = pick_button(target.get("buttons", []), action, button_text)
        if chosen is not None:
            _user32.PostMessageW(chosen["hwnd"], BM_CLICK, 0, 0)
            done = "clicked button '{}'".format(chosen["text"])
        elif action == "button":
            return {"ok": False, "error": "no button labelled '{}'".format(button_text),
                    "buttons": [b["text"] for b in target.get("buttons", [])]}
    if done is None:
        _user32.PostMessageW(target["hwnd"], WM_CLOSE, 0, 0)
        done = "sent WM_CLOSE"
    deadline = time.time() + wait
    closed = False
    while time.time() < deadline:
        if not _user32.IsWindow(target["hwnd"]) or not _user32.IsWindowVisible(target["hwnd"]):
            closed = True
            break
        time.sleep(0.05)
    return {"ok": True, "closed": closed, "did": done, "hwnd": target["hwnd"],
            "kind": target["kind"], "title": target["title"]}
