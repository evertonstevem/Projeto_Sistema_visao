import os

from args_parser import ArgsParser
from commands.capture import Capture
from commands.compare import Compare
from commands.process import Process
from commands.train import Train
from logger import Logger


class Python:
    """Main class for the Python program."""

    @classmethod
    def main(cls):
        """Main entry point of the program."""

        args = ArgsParser().parse_args()
        Logger(args.log)
        Logger.debug(f"Arguments passed: {str(args)}")
        Logger.info("Program started.")

        match args.mode:
            case "capture":
                if args.image_save_file is None:
                    # ! ERROR CODE 1
                    Logger.err_exit("Missing Save Path.", code=1)
                Capture.run(args.image_save_file)

            case "process":
                json_file = args.json_file
                Logger.debug("Starting process command.")
                if args.read_image is None:
                    # ! ERROR CODE 2
                    Logger.err_exit("Missing image path.", code=2)
                if json_file is None:
                    # ! ERROR CODE 3
                    Logger.err_exit("Missing JSON path.", code=3)
                if json_file.endswith(".json"):
                    Logger.warning("JSON file should not have extension, removing it.")
                    json_file = json_file[:-5]
                Process.run(args.read_image, json_file)

            case "compare":
                json_file = args.json_file
                template_file = args.template_file
                if args.image_save_file is None:
                    # ! ERROR CODE 1
                    Logger.err_exit("Missing Save Path.", code=1)
                if args.read_image is None:
                    # ! ERROR CODE 2
                    Logger.err_exit("Missing image path.", code=2)
                if json_file is None:
                    # ! ERROR CODE 3
                    Logger.err_exit("Missing JSON path.", code=3)
                if json_file.endswith(".json"):
                    Logger.warning("JSON file should not have extension, removing it.")
                    json_file = json_file[:-5]
                if template_file is None:
                    # ! ERROR CODE 3
                    Logger.err_exit("Missing JSON path.", code=3)
                if template_file.endswith(".json"):
                    Logger.warning("JSON file should not have extension, removing it.")
                    template_file = template_file[:-5]
                Compare.run(
                    args.image_save_file, args.read_image, json_file, template_file
                )

            case "train":
                json_file = args.json_file
                template_file = args.template_file
                if json_file is None:
                    # ! ERROR CODE 3
                    Logger.err_exit("Missing JSON path.", code=3)
                if json_file.endswith(".json"):
                    Logger.warning("JSON file should not have extension, removing it.")
                    json_file = json_file[:-5]
                if template_file is None:
                    # ! ERROR CODE 3
                    Logger.err_exit("Missing JSON path.", code=3)
                if template_file.endswith(".json"):
                    Logger.warning("JSON file should not have extension, removing it.")
                    template_file = template_file[:-5]
                Train.run(json_file, template_file)

        Logger.info("Program finished successfully.")
        return


if __name__ == "__main__":
    os.environ["OPENCV_LOG_LEVEL"] = "OFF"
    os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
    Python.main()
