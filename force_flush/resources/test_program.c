#include <stdio.h>
#include <windows.h>

int main()
{
    char buf[1024] = {0};
    setvbuf(stdout, buf, _IOFBF, 1024);
    while(TRUE)
    {
        printf("Testing this...");
        Sleep(2000);
    }
    return 0;
}