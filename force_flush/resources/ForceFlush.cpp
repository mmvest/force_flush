//ForceFlush.c
#include <windows.h>
#include <stdio.h>

BOOL WINAPI DllMain(
    HINSTANCE hinstDLL,  // handle to DLL module
    DWORD fdwReason,     // reason for calling function
    LPVOID lpvReserved )  // reserved
{

    switch( fdwReason ) 
    { 
        case DLL_PROCESS_ATTACH:
            if(fflush(stdout) != 0);
            {
                return FALSE;
            }
            break;
        default:
            return FALSE;
    }
    return TRUE;  // Successful DLL_PROCESS_ATTACH.
}