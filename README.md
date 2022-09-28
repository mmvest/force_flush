## About The Project

Force Flush is a python module that will flush the `stdout` buffer of a target process given the pid of that process. This is done by injecting a dll into the target process and then calling `fflush()` on `stdout`. This module will only work on Windows platforms. It was only tested on Windows 10.
<br>
<br>

### Why Would I Need Something Like This?

Honestly the use cases are pretty niche. One example is when using `subprocess.Popen()` with `stdout=subprocess.PIPE`. In this case, the `stdout` will buffer about 4096 bytes before printing (see [this stackoverflow post](https://stackoverflow.com/questions/1410849) for more information). If the process were to timeout during a follow-up `subprocess.communicate()` call, the `stdout` buffer is never flushed when the process is killed and the contents of that buffer are then lost. In this case, the `force_flush` module gives the ability to flush the `stdout` buffer of the target process before calling `kill()` on the process. This is particularly useful for processes that you have no control over in terms of code as well. 
<br>
<br>

### Aren't there built-in functions that will do this for you???

Through my testing, I have found that when using `Popen()` to run executables (rather than python scripts) that using the built-in functions that flush the `stdout` of the child process do not work. Changing the buffering settings also did not work (this is mentioned in that [SO post](https://stackoverflow.com/questions/1410849) linked earlier). So yes they are there but, no, they don't seem to work in this context.
<br>
<br>

## Disclaimer
Per usual, here is the standard disclaimer for this kind of stuff. This module uses DLL injection to achieve its goal. The injection code is provided for educational and ethical purposes and is not intended to be malicious in any degree. Some processes may not take kindly to DLL's being injected into them. I am not responsible and assume no liability for any misuse or damage caused by the concepts found in this code. 
<br>
<br>

## Getting Started
To use this module in your project, first download or clone the git repo:
```sh
git clone https://github.com/mmvest/force_flush.git
```
Now copy the force_flush directory from the repo into whatever project you need it. You can then import the flushing module into your python script using:
```py
from force_flush.flush_types import fflush_stdout
```
See [Usage](#usage) for examples of how to use this function.

### Prerequisites
* Python >3.10.0 -- visit [Python's official website](https://www.python.org/downloads/) to download latest version. No guarantees this will work on earlier versions.

* pywin32
  ```sh
  pip install pywin32
  ```
  OR
  ```sh
  python -m pip install pywin32
  ```
<br>
<br>

## Usage

Let us consider the example given to us in the [subprocess documentation](https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate):
```py
# Example from python docs
proc = subprocess.Popen(...)
try:
    outs, errs = proc.communicate(timeout=15)
except TimeoutExpired:
    proc.kill()
    outs, errs = proc.communicate()
    print(outs) # Will print nothing!
```
If we use this script to run the executable compiled from our [test_program.c](force_flush\resources\test_program.c), you will notice that when the TimeoutExpired exception is raised and the `proc.communicate()` call completes, the `outs` variable will be empty! So lets see what happens when we add the force_flush module to it!
```py
...
from force_flush.flush_types import fflush_stdout

# Modified example from python docs
proc = subprocess.Popen(...)
try:
    outs, errs = proc.communicate(timeout=15)
except TimeoutExpired:
    fflush_stdout(proc.pid)
    proc.kill()
    outs, errs = proc.communicate()
    print(outs) # Will now print what was in the stdout buffer!
```
Now the contents of the `stdout` buffer will be flushed and returned in the `outs` parameter of `proc.communicate()` when the `TimeoutExpired` exception occurs.
<br>
<br>
_See [demo.py](demo.py) and [force_flush.py](force_flush.py) for more examples of how to use this module._
<br>
<br>

## Roadmap
As this is just a personal project, my last goal will be to implement a "non-invasive" (though to be honest it is still kind of invasive) version of flushing another process's `stdout` buffer. This will be done by searching the system handle table for the `stdout` handle of the target process. See [this repo](https://github.com/SinaKarvandi/Process-Magics/tree/master/EnumAllHandles) for an example of how this may be possible.
<br>
<br>

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
