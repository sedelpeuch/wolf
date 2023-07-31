import os

from wolf_core import runner

# Import all the modules you want to be runnable here
if __name__ == "__main__":
    # for all files in the modules folder, import them
    abs_path = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(abs_path):
        if file.endswith(".py") and file not in ["main.py", "install.py", "__init__.py"]:
            __import__(f"wolf.{file[:-3]}")

    main_runner = runner.Runner(debug=False)
    main_runner.run()
