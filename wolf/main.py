import os
import sys
from wolf_core import runner

# Import all the modules you want to be runnable here
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "debug":
            debug = True
        else:
            debug = False
    else:
        debug = False

    abs_path = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(abs_path):
        if file.endswith(".py") and file not in ["main.py", "install.py", "__init__.py"]:
            __import__(f"wolf.{file[:-3]}")

    main_runner = runner.Runner(debug=debug)
    main_runner.run()
