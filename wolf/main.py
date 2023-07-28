from wolf_core import runner
import notion, example_job

if __name__ == "__main__":
    main_runner = runner.Runner(debug=False)
    main_runner.run()
