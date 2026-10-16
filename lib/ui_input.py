"""Screenshot and key input for the native windows of one process (Windows only).

A small replacement for driving Sublime Text through a general computer-use tool.
Like ``native_windows`` it needs no main thread and no ``sublime`` module, and every
entry point checks that the window belongs to the given process id first, so only
windows of Sublime Text itself are ever captured or sent input.

``screenshot`` renders the window with PrintWindow, so it also works for a window
that is behind others or not focused. ``press_key`` posts key messages to the window
without moving focus (method "post"), or, when asked, brings the window to the front
and sends real input (method "input"), restoring the previous foreground window.
"""

import struct
import sys
import time
import zlib

SUPPORTED = sys.platform == "win32"

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
PW_RENDERFULLCONTENT = 0x00000002
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0
CRLF = chr(13) + chr(10)
LF = chr(10)
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
KEYEVENTF_KEYUP = 0x0002
MAPVK_VK_TO_VSC = 0

_VK = {
    "enter": 0x0D, "return": 0x0D, "tab": 0x09, "escape": 0x1B, "esc": 0x1B,
    "space": 0x20, "backspace": 0x08, "delete": 0x2E, "del": 0x2E, "insert": 0x2D,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "ctrl": 0x11, "control": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B,
}
for _i in range(1, 25):
    _VK["f%d" % _i] = 0x6F + _i
_EXTENDED = {0x26, 0x28, 0x25, 0x27, 0x24, 0x23, 0x21, 0x22, 0x2D, 0x2E}

if SUPPORTED:
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _gdi32 = ctypes.windll.gdi32
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.IsWindow.argtypes = [wintypes.HWND]
    _user32.IsIconic.argtypes = [wintypes.HWND]
    _user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _user32.GetWindowDC.argtypes = [wintypes.HWND]
    _user32.GetWindowDC.restype = wintypes.HDC
    _user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    _user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    _user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    _user32.WindowFromPoint.argtypes = [wintypes.POINT]
    _user32.WindowFromPoint.restype = wintypes.HWND
    _user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    _user32.GetAncestor.restype = wintypes.HWND
    _user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    _user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    _user32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
    _user32.GetLastInputInfo.argtypes = [ctypes.c_void_p]

    class _LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    _user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    _user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_size_t]
    _gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    _gdi32.CreateCompatibleDC.restype = wintypes.HDC
    _gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    _gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    _gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    _gdi32.SelectObject.restype = wintypes.HGDIOBJ
    _gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    _gdi32.DeleteDC.argtypes = [wintypes.HDC]

    class _BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD),
                    ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
                    ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
                    ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]

    _gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
                                 ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]


def _pid(hwnd):
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _check(pid, hwnd):
    """Return an error dict unless hwnd is a live window of process pid."""
    if not SUPPORTED:
        return {"error": "ui tools are implemented for Windows only"}
    try:
        hwnd = int(hwnd)
    except (TypeError, ValueError):
        return {"error": "hwnd must be an integer from list_native_windows"}
    if not _user32.IsWindow(hwnd):
        return {"error": "hwnd {} is not a window".format(hwnd)}
    if _pid(hwnd) != pid:
        return {"error": "hwnd {} is not a window of this Sublime Text process".format(hwnd)}
    return None


def _png(width, height, rgb):
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def _scaled(rgb, w, h, scale, max_width):
    """Nearest-neighbour resize of packed RGB. ``scale`` multiplies the size (zoom in to read small
    text); ``max_width`` only ever shrinks. The longest side is capped at 4096 pixels."""
    try:
        s = float(scale) if scale else 1.0
        if max_width:
            s = min(s, float(max_width) / w)
    except (TypeError, ValueError):
        return {"error": "scale and max_width must be numbers"}
    if s <= 0:
        return {"error": "scale and max_width must be positive"}
    s = min(s, 4096.0 / max(w, h))
    nw, nh = max(1, int(round(w * s))), max(1, int(round(h * s)))
    if nw == w and nh == h:
        return {"rgb": rgb, "w": w, "h": h}
    cols = [min(w - 1, int(x / s)) * 3 for x in range(nw)]
    rows, last_y, last_row = [], None, b""
    for y in range(nh):
        sy = min(h - 1, int(y / s))
        if sy != last_y:
            src = rgb[sy * w * 3:(sy + 1) * w * 3]
            last_row = b"".join([src[c:c + 3] for c in cols])
            last_y = sy
        rows.append(last_row)
    return {"rgb": b"".join(rows), "w": nw, "h": nh}


def screenshot(pid, hwnd, settle_ms=200, region=None, scale=None, max_width=None):
    """PNG bytes of window ``hwnd`` of process ``pid`` (works for background windows),
    or an error dict. ``region`` is an optional {x, y, width, height} in pixels of the
    window picture; the PNG then holds only that part. ``scale`` (zoom) and ``max_width``
    (shrink) resize the result."""
    err = _check(pid, hwnd)
    if err:
        return err
    hwnd = int(hwnd)
    _settle(settle_ms)
    if _user32.IsIconic(hwnd):
        return {"error": "the window is minimized; a minimized window cannot be captured"}
    rect = wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width, height = rect.right - rect.left, rect.bottom - rect.top
    if width <= 0 or height <= 0:
        return {"error": "the window has no size"}
    wdc = _user32.GetWindowDC(hwnd)
    mdc = _gdi32.CreateCompatibleDC(wdc)
    bmp = _gdi32.CreateCompatibleBitmap(wdc, width, height)
    old = _gdi32.SelectObject(mdc, bmp)
    try:
        if not _user32.PrintWindow(hwnd, mdc, PW_RENDERFULLCONTENT):
            return {"error": "PrintWindow failed for hwnd {}".format(hwnd)}
        bih = _BITMAPINFOHEADER()
        bih.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bih.biWidth, bih.biHeight = width, -height  # top-down
        bih.biPlanes, bih.biBitCount, bih.biCompression = 1, 32, BI_RGB
        buf = ctypes.create_string_buffer(width * height * 4)
        got = _gdi32.GetDIBits(mdc, bmp, 0, height, buf, ctypes.byref(bih), DIB_RGB_COLORS)
        if not got:
            return {"error": "GetDIBits failed"}
        bgra = buf.raw
        rgb = bytearray(width * height * 3)
        rgb[0::3] = bgra[2::4]
        rgb[1::3] = bgra[1::4]
        rgb[2::3] = bgra[0::4]
        out_w, out_h = width, height
        if region:
            try:
                rx, ry = max(0, int(region.get("x", 0))), max(0, int(region.get("y", 0)))
                rw = min(width - rx, int(region.get("width", width)))
                rh = min(height - ry, int(region.get("height", height)))
            except (AttributeError, TypeError, ValueError):
                return {"error": "region must be {x, y, width, height} in integer pixels"}
            if rw <= 0 or rh <= 0:
                return {"error": "region is outside the {}x{} window picture".format(width, height)}
            rows = [bytes(rgb[((ry + r) * width + rx) * 3:((ry + r) * width + rx + rw) * 3]) for r in range(rh)]
            rgb, out_w, out_h = b"".join(rows), rw, rh
        done = _scaled(bytes(rgb), out_w, out_h, scale, max_width)
        if "error" in done:
            return done
        return {"png": _png(done["w"], done["h"], done["rgb"]), "width": done["w"], "height": done["h"]}
    finally:
        _gdi32.SelectObject(mdc, old)
        _gdi32.DeleteObject(bmp)
        _gdi32.DeleteDC(mdc)
        _user32.ReleaseDC(hwnd, wdc)


def _bring_to_front(hwnd, previous):
    """Try to make hwnd the foreground window. Windows only lets the foreground process do
    that, so share the foreground thread's input queue for a moment (AttachThreadInput)."""
    me = ctypes.windll.kernel32.GetCurrentThreadId()
    fg_thread = _user32.GetWindowThreadProcessId(previous, None) if previous else 0
    attached = False
    if fg_thread and fg_thread != me:
        attached = bool(_user32.AttachThreadInput(me, fg_thread, True))
    try:
        _user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            _user32.AttachThreadInput(me, fg_thread, False)


def _settle(ms):
    """Wait so posted input has been handled before the next step (default is short)."""
    try:
        ms = max(0, min(int(ms), 5000))
    except (TypeError, ValueError):
        ms = 150
    if ms:
        time.sleep(ms / 1000.0)


def _vk(name):
    n = str(name).strip().lower()
    if n in _VK:
        return _VK[n]
    if len(n) == 1:
        if n.isalnum():
            return ord(n.upper())
        res = _user32.VkKeyScanW(ord(n))
        if res != -1:
            return res & 0xFF
    return None


def _lparam(vk, up=False, alt=False):
    scan = _user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
    lp = 1 | (scan << 16)
    if vk in _EXTENDED:
        lp |= 1 << 24
    if alt:
        lp |= 1 << 29
    if up:
        lp |= (1 << 30) | (1 << 31)
    return lp


def _client_width_hint(hwnd):
    """A title-bar x position well inside the window (the middle of its width)."""
    rect = wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return max(1, (rect.right - rect.left) // 2)


def press_key(pid, hwnd, key, mods=None, method="post", settle_ms=150, min_idle_s=8.0, wait_idle_s=0):
    """Send one key (with optional modifiers) to window ``hwnd`` of process ``pid``.

    method "post": WM_KEYDOWN/WM_KEYUP (and WM_CHAR for a printable key with no ctrl/alt)
    are posted to the window; focus is not moved, but modifiers are not seen by Sublime.
    method "input": real key events, which carry modifiers. The window must be in front; if it
    is not, it is activated with a real click on its title bar, which is only done when the
    person at the computer has been idle for ``min_idle_s`` seconds."""
    err = _check(pid, hwnd)
    if err:
        return err
    hwnd = int(hwnd)
    vk = _vk(key)
    if vk is None:
        return {"error": "unknown key {!r}".format(key)}
    mod_vks = []
    for m in (mods or []):
        mv = _VK.get(str(m).lower())
        if mv not in (0x11, 0x10, 0x12, 0x5B):
            return {"error": "unknown modifier {!r}; use ctrl, shift, alt or win".format(m)}
        mod_vks.append(mv)
    if method == "input":
        # Real key events land wherever the person's focus is, so never send them while they are typing.
        idle = wait_for_idle(min_idle_s, wait_idle_s)
        if idle < min_idle_s:
            return {"error": "the person at the computer is using the mouse or keyboard (idle {:.1f}s, "
                             "need {:.1f}s); real keys would collide with their typing. Pass wait_idle_s "
                             "to wait for them to stop, or use method 'post'".format(idle, min_idle_s),
                    "idle_seconds": round(idle, 1)}
        previous = _user32.GetForegroundWindow()
        if previous != hwnd:
            _bring_to_front(hwnd, previous)
            time.sleep(0.15)
        if _user32.GetForegroundWindow() != hwnd:
            # Windows refuses to let a background process take the foreground. A real click on
            # the window's title bar activates it, but that moves the person's pointer, so it is
            # gated on them being idle (and on the window really being under that point).
            res = click(pid, hwnd, _client_width_hint(hwnd), 16, "left", False, min_idle_s, 150, wait_idle_s)
            if "error" in res:
                return {"error": "the window is not in front and could not be activated: " + res["error"]}
            time.sleep(0.15)
        # Real key events go to whichever window is in front, not to hwnd: never send
        # them unless the target really is in front.
        if _user32.GetForegroundWindow() != hwnd:
            return {"error": "could not bring hwnd {} to the front, so no keys were sent; use "
                             "method 'post' for keys without modifiers".format(hwnd)}
        for mv in mod_vks:
            _user32.keybd_event(mv, 0, 0, 0)
        _user32.keybd_event(vk, _user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC), 0, 0)
        _user32.keybd_event(vk, _user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC), KEYEVENTF_KEYUP, 0)
        for mv in reversed(mod_vks):
            _user32.keybd_event(mv, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.1)
        if previous and previous != hwnd and _user32.IsWindow(previous):
            _user32.SetForegroundWindow(previous)
        return {"ok": True, "method": "input", "hwnd": hwnd}
    if method != "post":
        return {"error": "method must be 'post' or 'input'"}
    alt = 0x12 in mod_vks
    ch = str(key)
    if len(ch) == 1 and not (0x11 in mod_vks or alt):
        # A printable character with no ctrl/alt: Sublime turns a posted key-down into a
        # character itself (using the real keyboard state, so no shift), so sending both
        # would type it twice. Post the character alone and apply shift ourselves.
        _user32.PostMessageW(hwnd, WM_CHAR, ord(ch.upper() if 0x10 in mod_vks else ch), _lparam(vk))
        _settle(settle_ms)
        return {"ok": True, "method": "post", "hwnd": hwnd, "sent": "character"}
    down, up = (WM_SYSKEYDOWN, WM_SYSKEYUP) if alt else (WM_KEYDOWN, WM_KEYUP)
    for mv in mod_vks:
        _user32.PostMessageW(hwnd, WM_SYSKEYDOWN if mv == 0x12 else WM_KEYDOWN, mv, _lparam(mv, alt=alt))
    _user32.PostMessageW(hwnd, down, vk, _lparam(vk, alt=alt))
    _user32.PostMessageW(hwnd, up, vk, _lparam(vk, up=True, alt=alt))
    for mv in reversed(mod_vks):
        _user32.PostMessageW(hwnd, WM_SYSKEYUP if mv == 0x12 else WM_KEYUP, mv, _lparam(mv, up=True, alt=alt))
    _settle(settle_ms)
    return {"ok": True, "method": "post", "hwnd": hwnd, "sent": "key"}


def type_text(pid, hwnd, text, settle_ms=150):
    """Type ``text`` into window ``hwnd`` of process ``pid`` as WM_CHAR messages (no focus
    change). Newlines are sent as Return."""
    err = _check(pid, hwnd)
    if err:
        return err
    hwnd = int(hwnd)
    text = str(text)
    if len(text) > 2000:
        return {"error": "text is limited to 2000 characters per call"}
    for ch in text.replace(CRLF, LF):
        if ch == LF:
            _user32.PostMessageW(hwnd, WM_KEYDOWN, 0x0D, _lparam(0x0D))
            _user32.PostMessageW(hwnd, WM_KEYUP, 0x0D, _lparam(0x0D, up=True))
            continue
        code = ord(ch)
        if code > 0xFFFF:  # outside the BMP: send the UTF-16 surrogate pair
            code -= 0x10000
            for unit in (0xD800 + (code >> 10), 0xDC00 + (code & 0x3FF)):
                _user32.PostMessageW(hwnd, WM_CHAR, unit, 1)
        else:
            _user32.PostMessageW(hwnd, WM_CHAR, code, 1)
    _settle(settle_ms)
    return {"ok": True, "method": "post", "hwnd": hwnd, "characters": len(text)}


def idle_seconds():
    """Seconds since the person at the keyboard last pressed a key or moved the mouse."""
    li = _LASTINPUTINFO()
    li.cbSize = ctypes.sizeof(_LASTINPUTINFO)
    _user32.GetLastInputInfo(ctypes.byref(li))
    return (ctypes.windll.kernel32.GetTickCount() - li.dwTime) / 1000.0


def wait_for_idle(min_idle_s, wait_idle_s=0):
    """Return the idle seconds once they reach ``min_idle_s``, waiting up to ``wait_idle_s`` seconds for
    the person at the computer to stop typing or moving the mouse. Returns the last value seen on timeout."""
    try:
        wait = max(0.0, min(float(wait_idle_s or 0), 120.0))
        need = float(min_idle_s)
    except (TypeError, ValueError):
        return idle_seconds()
    end = time.time() + wait
    idle = idle_seconds()
    while idle < need and time.time() < end:
        time.sleep(0.25)
        idle = idle_seconds()
    return idle


def click(pid, hwnd, x, y, button="left", double=False, min_idle_s=8.0, settle_ms=250, wait_idle_s=0):
    """Click at picture position (x, y) of window ``hwnd`` of process ``pid`` with the REAL mouse.

    Sublime draws its own editor, palette and popups and ignores posted mouse messages, so a
    real click is the only way to reach them. That moves the pointer of the person at the computer,
    so it is refused unless they have been idle for ``min_idle_s`` seconds, and refused unless the
    target window is the window under the point at that moment (a window in front of it would take
    the click). The pointer is put back afterwards. x and y are pixels in the picture
    ``screenshot`` returns."""
    err = _check(pid, hwnd)
    if err:
        return err
    hwnd = int(hwnd)
    try:
        x, y = int(x), int(y)
        min_idle_s = float(min_idle_s)
    except (TypeError, ValueError):
        return {"error": "x and y must be integers (pixels in the window picture)"}
    if button not in ("left", "right"):
        return {"error": "button must be left or right"}
    if _user32.IsIconic(hwnd):
        return {"error": "the window is minimized"}
    rect = wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    if not (0 <= x < rect.right - rect.left and 0 <= y < rect.bottom - rect.top):
        return {"error": "({}, {}) is outside the window ({} x {})".format(
            x, y, rect.right - rect.left, rect.bottom - rect.top)}
    idle = wait_for_idle(min_idle_s, wait_idle_s)
    if idle < min_idle_s:
        return {"error": "the person at the computer is using the mouse or keyboard (idle {:.1f}s, "
                         "need {:.1f}s); a real click would move their pointer. Try again later, pass "
                         "wait_idle_s to wait for them to stop, or "
                         "use keys / editor commands instead".format(idle, min_idle_s),
                "idle_seconds": round(idle, 1)}
    sx, sy = rect.left + x, rect.top + y
    under = _user32.WindowFromPoint(wintypes.POINT(sx, sy))
    root = _user32.GetAncestor(under, 2) if under else None  # GA_ROOT
    if int(root or 0) != hwnd:
        return {"error": "another window is in front of that point (window {} is under it, not {}); "
                         "no click was sent".format(int(root or 0), hwnd)}
    old = wintypes.POINT()
    _user32.GetCursorPos(ctypes.byref(old))
    if button == "left":
        down, up = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    else:
        down, up = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    try:
        _user32.SetCursorPos(sx, sy)
        time.sleep(0.12)
        _user32.SetCursorPos(sx + 1, sy)
        time.sleep(0.04)
        _user32.SetCursorPos(sx, sy)
        time.sleep(0.04)
        for _ in range(2 if double else 1):
            _user32.mouse_event(down, 0, 0, 0, 0)
            time.sleep(0.05)
            _user32.mouse_event(up, 0, 0, 0, 0)
            time.sleep(0.05)
        _settle(settle_ms)
    finally:
        _user32.SetCursorPos(old.x, old.y)
    return {"ok": True, "method": "pointer", "hwnd": hwnd, "screen": [sx, sy], "idle_seconds": round(idle, 1)}


def hover(pid, hwnd, x, y, dwell_ms=900, hold_ms=0, capture=False, min_idle_s=8.0, wait_idle_s=0, shot_opts=None):
    """Move the real pointer to picture position (x, y) of window ``hwnd`` and leave it there for
    ``dwell_ms`` (so hover popups can appear), optionally taking a picture while it is there, then
    keep it ``hold_ms`` longer and put it back. Same gates as ``click``: refused unless the person at
    the computer is idle, and unless the target window is the window under the point."""
    err = _check(pid, hwnd)
    if err:
        return err
    hwnd = int(hwnd)
    try:
        x, y = int(x), int(y)
        dwell = max(0, min(int(dwell_ms), 5000))
        hold = max(0, min(int(hold_ms), 5000))
        min_idle_s = float(min_idle_s)
    except (TypeError, ValueError):
        return {"error": "x, y, dwell_ms and hold_ms must be numbers"}
    if _user32.IsIconic(hwnd):
        return {"error": "the window is minimized"}
    rect = wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    if not (0 <= x < rect.right - rect.left and 0 <= y < rect.bottom - rect.top):
        return {"error": "({}, {}) is outside the window".format(x, y)}
    idle = wait_for_idle(min_idle_s, wait_idle_s)
    if idle < min_idle_s:
        return {"error": "the person at the computer is using the mouse or keyboard (idle {:.1f}s, "
                         "need {:.1f}s); hovering moves their pointer. Try again later or pass "
                         "wait_idle_s".format(idle, min_idle_s),
                "idle_seconds": round(idle, 1)}
    sx, sy = rect.left + x, rect.top + y
    under = _user32.WindowFromPoint(wintypes.POINT(sx, sy))
    root = _user32.GetAncestor(under, 2) if under else None
    if int(root or 0) != hwnd:
        return {"error": "another window is in front of that point (window {} is under it, not {}); "
                         "the pointer was not moved".format(int(root or 0), hwnd)}
    old = wintypes.POINT()
    _user32.GetCursorPos(ctypes.byref(old))
    shot = None
    try:
        _user32.SetCursorPos(sx - 3, sy)
        time.sleep(0.05)
        _user32.SetCursorPos(sx, sy)
        time.sleep(dwell / 1000.0)
        if capture:
            opts = shot_opts or {}
            shot = screenshot(pid, hwnd, 0, opts.get("region"), opts.get("scale"), opts.get("max_width"))
        time.sleep(hold / 1000.0)
    finally:
        _user32.SetCursorPos(old.x, old.y)
    out = {"ok": True, "method": "pointer", "hwnd": hwnd, "screen": [sx, sy], "idle_seconds": round(idle, 1)}
    if shot is not None:
        out["shot"] = shot
    return out
