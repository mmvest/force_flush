## About The Project

Force Flush is a python module that will flush the `stdout` buffer of a target process given the pid of that process. This is done by injecting a dll into the target process and then calling `fflush()` on `stdout`. This module will only work on Windows platforms. It was only tested on Windows 10.
<br>
<br>

### Why Would I Need Something Like This?

Honestly the use cases are pretty niche. One example is for use with the `subprocess` module. Consider an example given to us in the [subprocess documentation](https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate):
```py
# Slightly modified example from python docs
proc = subprocess.Popen(..., stdout=subprocess.PIPE, ...)
try:
    outs, errs = proc.communicate(timeout=15)
except TimeoutExpired:
    proc.kill()
    outs, errs = proc.communicate()
    print(outs.decode('ascii', errors='ignore'))
```
If we use this script to run the executable compiled from [demo_executable.c](force_flush\resources\demo_executable.c), you will notice that when the `TimeoutExpired` exception is raised and the `proc.communicate()` call completes, the `outs` variable will be empty! When using  `subprocess.Popen()` with `stdout=subprocess.PIPE` as an argument, the process will buffer some number of bytes before actually writing to `stdout` (see [this stackoverflow post](https://stackoverflow.com/questions/1410849) I stumbled upon for more information). If the `communicate()` call timesout while waiting for the process to complete execution, the `TimeoutExpired` exception will be raised and the `stdout` buffer of that process is never flushed when `proc.kill()` is run. In this case, the `force_flush` module gives the ability to flush the `stdout` buffer of the target process before calling `proc.kill()`. This is particularly useful for logging and debugging the process being executed and also for processes that you have no control over in terms of code. 
<br>
<br>

### Aren't there built-in `subprocess` functions that will do this for you???

Through my testing I have found that when using `Popen()` to run executables, using the built-in functions that flush the `stdout` of the child process does not work. Changing the buffering settings in the `Popen()` call also did not work (this is mentioned in that [SO post](https://stackoverflow.com/questions/1410849) linked earlier). So yes the built-in functions are there but, no, they don't seem to work in this context. I created this module to provide an easy-to-use function call that will flush the `stdout` buffer for you so when `communicate()` returns you can retrieve what was supposed to be written to stdout before the process was killed. 
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
<br>
<br>

### Prerequisites

* Windows 10
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

Now consider the [example from earlier](#why-would-i-need-something-like-this) except it now includes the `force_flush` module:
```py
...
from force_flush.flush_types import fflush_stdout

# Modified example from python docs
proc = subprocess.Popen(..., stdout = subprocess.PIPE)
try:
    outs, errs = proc.communicate(timeout=15)
except TimeoutExpired:
    fflush_stdout(proc.pid)
    proc.kill()
    outs, errs = proc.communicate()
    print(outs.decode('ascii', errors='ignore'))
```
After calling `fflush_stdout()` the contents of the target process's `stdout` buffer will now be written and returned in the `outs` parameter of `proc.communicate()`.
<br>
<br>
_See [demo.py](demo.py) and [force_flush.py](force_flush.py) for more examples of how to use this module._
<br>
<br>

### Demo
To use the demo, first compile `demo_executable.c` using your compiler of choice. For example, from the repo root directory use:
```sh
gcc force_flush\resources\demo_executable.c -o force_flush\resources\demo_executable.exe
```
Now you can simply call demo.py directly:
```sh
python demo.py
```

Output should be similar to the following:
```sh
======== DEMO WHEN BUFFER NOT FLUSHED ========
stdout when not flushed: 
======== DEMO WHEN BUFFER IS FLUSHED ========
stdout when buffer is flushed: Testing this...Testing this...
```
<br>

### How to Use `force_flush.py` Utility Script

The `force_flush.py` utility script is just a quick script that takes a PID as an input argument and will attempt to flush the stdout of the correlating process. Use this script like so:
```sh
python force_flush.py <pid of target process>
```
<br>
<br>


## Roadmap
As this is just a personal project, my last goal will be to implement a "non-invasive" (though to be honest it is still kind of invasive) version of flushing another process's `stdout` buffer. This will be done by searching the system handle table for the `stdout` handle of the target process. See [this repo](https://github.com/SinaKarvandi/Process-Magics/tree/master/EnumAllHandles) for an example of how this may be possible.
<br>
<br>

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
