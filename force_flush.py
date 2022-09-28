'''
module: force_flush.py



References:
1) https://learn.microsoft.com/en-us/windows/win32/secauthz/enabling-and-disabling-privileges-in-c--    --- How to enable/disable privileges
2) https://learn.microsoft.com/en-us/windows/win32/secauthz/privileges                                  --- How privileges work and why we need to get the LUID of a specific privilege
3) https://learn.microsoft.com/en-us/windows/win32/secauthz/privilege-constants#SE_DEBUG_NAME           --- Why we need the SE_DEBUG_PRIVILEGE -> It is required to adjust the memory of a process owned by another account
4) https://learn.microsoft.com/en-us/windows/win32/Memory/memory-protection-constants                   --- List of memory protection constants
5) https://learn.microsoft.com/en-us/windows/win32/secauthz/access-rights-for-access-token-objects      --- List of access right for access-token objects
6) https://python.plainenglish.io/interacting-with-the-windows-api-with-python-a819427ab39a             --- Basic reference for injection process

'''
import argparse
import traceback

from force_flush.flush_types import fflush_stdout
def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Flush the stdout of the given process")
    parser.add_argument('pid', type=int, help="The PID of the target process")
    
    # TODO: Arguments to add in the future given I add additional functionality
    # parser.add_argument('method', type=string, help="The method by which to flush the target process stdout")
    # parser.add_argument('fd', type=string, help="The file descriptor/HANDLE value to flush if not flushing stdout")
    
    return parser

def main(args):
    pid = args.pid
    
    try:
        fflush_stdout(pid)
    except OSError as exc:
        print(str(exc))
    except:
        traceback.print_exc()



if __name__ == "__main__":
    main(get_arg_parser().parse_args())
