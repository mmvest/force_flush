import sys
from typing import Union, Tuple

from pywintypes import error as pywinerror
from ctypes.wintypes import HANDLE
from win32api import GetCurrentProcess, GetProcAddress, GetModuleHandle
from win32process import WriteProcessMemory, VirtualAllocEx, CreateRemoteThread
from win32security import LookupPrivilegeValue, OpenProcessToken, AdjustTokenPrivileges, GetTokenInformation, TokenPrivileges, LookupPrivilegeName
from win32con import TOKEN_ADJUST_PRIVILEGES, TOKEN_QUERY, SE_PRIVILEGE_ENABLED, MEM_COMMIT, MEM_RESERVE, PAGE_EXECUTE_READWRITE, NULL

from force_flush import KERNEL32_DLL_NAME, LOAD_LIB_NAME

def get_error_info(exc:pywinerror) -> str:
    """ Return a useful string representation of a pywintypes.error.

    Arguments
    - exc --- the pywintypes.error that was raised from an exception
    """
    __, __, exc_tb = sys.exc_info() # Using this just to get the line number of the exception
    line_number = exc_tb.tb_lineno
    error_code = exc.args[0]
    function_that_raised_error = exc.args[1]
    error_reason = exc.args[2]
    return f"Exception raised during execution of {function_that_raised_error} on line {line_number}. Error {error_code} - {error_reason}"

def check_access_token_for_privilege(token_handle:Union[HANDLE, int], privilege_to_check:Union[int, str]) -> bool:
    """Check if a given access token has access to a specfic privilege.

    Returns True if token has access to a privilege and False otherwise

    Arguments
    - token_handle          --- handle or handle int value to the access token to check
    - privilege_to_check    --- the LUID or string name of a privilege
    """
    
    # Validate input...
    if not isinstance(token_handle, (HANDLE, int)):
        raise TypeError("The 1st argument (token_handle) of the check_access_token_for_privilege function must be \
                            a valid 'HANDLE' or an 'int' handle value of the access token to check.")        

    if not isinstance(privilege_to_check, (int, str)):
        raise TypeError("The 2nd argument (privilege_to_check) of the check_access_token_for_privilege function must be \
                            an 'int' LUID or a 'str' name of the access token privilege to check for.")
    
    try:
        process_privileges = GetTokenInformation(       # Returns PyTOKEN_PRIVILEGES
            token_handle,                               # Handle to the access token
            TokenPrivileges                             # What information we want to retrieve
        )
    except pywinerror as exc:
        raise OSError(f"[!] Failed to retrieve token information. {get_error_info(exc)}")

    for privilege in process_privileges:
        privilege_luid = privilege[0]
        privilege_name = LookupPrivilegeName(None, privilege_luid)
        #print(f"{privilege_name} -- {privilege[1]}")  # uncomment this if you want to print every privilege
        if privilege_to_check == privilege_luid or privilege_to_check == privilege_name:
            return True
    
    return False

def set_privilege(privilege):
    """
    Enable the privilege in the current process access token specified by privilege.

    Returns the old privileges before modification in the form of a PyTOKEN_PRIVILEGES
    
    Arguments
    - privilege --- the name of the privilege to enable in this process's access token (e.g. "SeDebugPrivilege" among others)
                    OR a PyTOKEN_PRIVILEGES object. Assumes object passed is PyTOKEN_PRIVILEGES if string name is not passed in.
    """

    # If we are given a string name for a privilege, in order to set the process access token to have that privilege, first 
    # find the unique ID (LUID) for the privilege based on that name.
    if isinstance(privilege, str):
        try:
            priv_LUID = LookupPrivilegeValue(   # Returns an int representation of the LUID
                None,                           # System name of where to retrieve the privilege; Setting as 'None' will attempt to find the privilege name on the local system
                privilege                       # Name of the privilege to retrieve
                ) 
        except pywinerror as exc:
            raise OSError(f"[!] Failed to retrieve the LUID for '{privilege}'. {get_error_info(exc)}")
    
    # Now open our process token so we have the ability to adjust our access token privileges.
    try:
        cur_token_handle = OpenProcessToken(    # Returns PyHandle for the access token
            GetCurrentProcess(),                # Get a handle to the current process
            TOKEN_ADJUST_PRIVILEGES|TOKEN_QUERY # Desired access; We want to adjust privileges. See reference (5) for more info
            )
    except pywinerror as exc:
        raise OSError(f"[!] Failed to open the process access token. {get_error_info(exc)}")

    # Now adjust our process token privileges, passing in the LUID for the specific privilege. See reference (1) and (2) for more information.
    # If we have a PyTOKEN_PRIVILEGES object for the input, then we just pass that object instead
    if isinstance(privilege, str):
        desired_token_privileges = [(priv_LUID, SE_PRIVILEGE_ENABLED)]
    else:
        desired_token_privileges = privilege

    try:
        prev_token = AdjustTokenPrivileges(     # Returns PyTOKEN_PRIVILEGES
            cur_token_handle,                   # Handle to the token we want to adjust
            False,                              # Flag for disabling all privileges; Set this to False since we do NOT want to disable privileges
            desired_token_privileges            # The new state of the token we want to adjust to.
            )
    except pywinerror as exc:
        raise OSError(f"[!] Failed to adjust process access token. {get_error_info(exc)}")

    return prev_token

def inject_data(target_process:Union[HANDLE, int], data:bytes):
    """ Injects data into the target process.
    
    Returns a tuple (long, int) containing the address of the injected data and the number of bytes written at that address respectively.

    Arguments
    - target_process    --- HANDLE to or 'int' handle value of the target process to inject data into
    - data              --- bytes to inject into the target process

    """
    # Allocate enough memory in the target process to write the data into the process
    try:
        mem_location = VirtualAllocEx(  # Returns address of allocated memory as a long
            target_process,             # Process handle to allocate reserve + commit memory region in
            NULL,                       # Starting address of memory; NULL will let the function determine where to allocate memory region
            len(data),                  # Length of what needs to be written inside the allocated space
            MEM_COMMIT|MEM_RESERVE,     # Type of memory allocation; We want to commit and reserve the memory range
            PAGE_EXECUTE_READWRITE      # The memory protection for the allocated memory
            )
    except pywinerror as exc:
        raise OSError(f"[!] Failed to allocate memory in target process. {get_error_info(exc)}")

    # We can now call WriteProcessMemory to write the data to the process.
    try:
        num_bytes_written = WriteProcessMemory(         # Returns int number of bytes written
            target_process,                             # Handle to the process we are writing to
            mem_location,                               # Location we are writing to
            data,                                       # Data we are writing to that location
        )
    except pywinerror as exc:
        raise OSError(f"[!] Failed to write {data} to target process at address {mem_location:x}. {get_error_info(exc)}")

    return (mem_location, num_bytes_written)

def run_dll_injected_by_name(target_process:Union[HANDLE, int], dll_name_address) -> Tuple[HANDLE, int]:
    """Run a dll within the context of the target process by using an address location that contains the name of the dll.

    Returns (PyHANDLE, int) where 'PyHandle' is the handle for the thread created inside the target process and 'int' is the thread id

    Arguments
    - target_process    --- HANDLE to, or 'int' handle value of, the target process to run the dll in
    - dll_name_address  --- Address containing the name of the dll to run inside the target process
    """

     # We need to get the memory location of LoadLibraryA so we can load our dll using its name that has been injected
     # into the target process. This function is from kernel32.dll which means that every PE should have this function.
    try:
        load_lib_address = GetProcAddress(          # Returns int address of the function we are looking for
            GetModuleHandle(KERNEL32_DLL_NAME),     # The Handle of the module containing the function we are retrieving the address of
            LOAD_LIB_NAME                           # The name of the function we wish to retrieve the address of
            )
    except pywinerror as exc:
        raise OSError(f"[!] Failed to find LoadLibraryA location. {get_error_info(exc)}")

    # Now we need to run our dll within the context of the target process by calling CreateRemoteThread and passing it the address of LoadLibraryA 
    # and the address of our DLL name.
    try:
        thread_handle, thread_id = CreateRemoteThread(
            target_process,     # Target process to create thread in
            None,               # Thread attributes
            0,                  # Stack size; 0 means default size
            load_lib_address,   # Entry point of the thread
            dll_name_address,   # Argument passed to the entry point
            0                   # Flags; 0 means to execute thread immediately
        )
    except pywinerror as exc:
        raise OSError(f"[!] Failed to create remote thread in target process at entry point {load_lib_address:x} with arguments at address {dll_name_address}. {get_error_info(exc)}")

    return (thread_handle, thread_id)