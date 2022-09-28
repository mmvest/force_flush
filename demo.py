import subprocess
import os
from force_flush.flush_types import fflush_stdout

args = (os.path.dirname(__file__) + "\\force_flush\\resources\\test_program.exe").split()
timeout_in_seconds = 4

# Modified version of the example from python docs
# This will NOT return the standard out buffer because the buffer was never flushed
print("======== DEMO WHEN BUFFER NOT FLUSHED ========")
proc = subprocess.Popen(args, stdout=subprocess.PIPE)
try:
    outs, errs = proc.communicate(timeout=timeout_in_seconds)
except subprocess.TimeoutExpired:
    proc.kill()
    outs, errs = proc.communicate()
    print(f"stdout when not flushed: {outs.decode('ascii', errors='ignore')}")

# This WILL return stdout buffer because we are injecting our code and forcing it to flush
print("======== DEMO WHEN BUFFER IS FLUSHED ========")
proc = subprocess.Popen(args, stdout=subprocess.PIPE)
try:
    outs, errs = proc.communicate(timeout=timeout_in_seconds)
except subprocess.TimeoutExpired:
    fflush_stdout(proc.pid)
    proc.kill()
    outs, errs = proc.communicate()
    print(f"stdout when buffer is flushed: {outs.decode('ascii', errors='ignore')}")