from enum import Enum
import os
from pywintypes import error as pywinerror
from win32api import OpenProcess
from win32con import PROCESS_ALL_ACCESS, SE_DEBUG_NAME
from win32event import WaitForSingleObject

from force_flush import INJECT_DLL_NAME
from force_flush.helpers import *

WAIT_INFINITE = 0xFFFFFFFF  # Use this when calling WaitForSingleObject as the timeout parameter

class FlushType(Enum):
    INJECTION       = 1
    # HANDLE_TABLE    = 2   # Not yet implemented

def fflush_stdout_by_injection(pid:int) -> None:
    """ Flush the stdout buffer of a target process by injecting ForceFlush.dll into the process.

    Arguments
    - pid --- The pid of the target process that contains the stdout buffer to be flushed
    """

    # First, set our access token privileges to SeDebugPrivileges so we can manipulate the memory of another process.
    # See reference (3) for more information.
    prev_token_privileges = set_privilege(SE_DEBUG_NAME)

    # Next, open the target process to retrieve a handle to that process.
    try:
        target_process = OpenProcess(   # Returns PyHANDLE
            PROCESS_ALL_ACCESS,         # Privileges requested; Should be given because we have SeDebugPrivilege enabled
            False,                      # Inherit flag; we do not need this handle to be inheritable
            pid                         # The PID of the target process we want to inject our code into
        )
    except pywinerror as exc:
        raise OSError(f"[!] Failed to open target process. {get_error_info(exc)}")

    # Now inject the name of our DLL into the target process
    dll_name_to_inject = bytes(os.path.dirname(__file__), encoding='ascii') + INJECT_DLL_NAME
    mem_location, __ = inject_data(target_process, dll_name_to_inject)

    # Now run our dll within the context of the target process
    thread_handle, __ = run_dll_injected_by_name(target_process, mem_location)

    # Wait for that thread to finish execution
    try:
        wait_result = WaitForSingleObject(thread_handle, WAIT_INFINITE)
    except pywinerror as exc:
        raise OSError(f"[!] Failed to wait for thread to finish execution. {get_error_info(exc)}")

    # Lastly, restore access token privileges
    set_privilege(prev_token_privileges)

# TODO: Add functionality that does NOT require injection, but follows a method similar to that found here: https://github.com/SinaKarvandi/Process-Magics/tree/master/EnumAllHandles
# def flush_stdout_by_system_handle_table():
#     pass

def fflush_stdout(pid:int, method:int = FlushType.INJECTION):
    if method == FlushType.INJECTION:
        fflush_stdout_by_injection(pid)
    
    # TODO: Add others here