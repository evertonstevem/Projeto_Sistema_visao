from argparse import ArgumentParser
from typing import Literal, NamedTuple, Optional


class ArgsParser(ArgumentParser):
    """Argument parser for the Python program."""

    _PROG = "Image_Processing"
    _DESCRIPTION = "Program to capture, process, and save images from the Baumer cam."

    def __init__(self):
        super().__init__(prog=self._PROG, description=self._DESCRIPTION)

        self.add_argument(
            "mode",
            help="Mode to run the script in.",
            choices=["capture", "process", "train", "compare"],
        )
        self.add_argument(
            "-s",
            "--image_save_file",
            help="File to save the image to (capture|compare).",
            type=str,
            required=False,
        )
        self.add_argument(
            "-r",
            "--read_image",
            help="Path to image that will be read and processed "
            + "(process|compare).",
            type=str,
        )
        self.add_argument(
            "-j",
            "--json_file",
            help="Path and only name of the to JSON file that will be read or written,"
            + " without the .json extension (process|compare|train).",
            type=str,
        )
        self.add_argument(
            "-l",
            "--log",
            help="Logging level to use.",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="WARNING",
        )
        self.add_argument(
            "-t",
            "--template",
            help="Path to the template json that will be used for template matching"
            + " without the .json extension (compare|train).",
            type=str,
        )

    def parse_args(self):
        class _Args(NamedTuple):
            """
            Class to hold the arguments passed to the program and give them a type.
            """

            mode: Literal["capture", "process", "train", "compare"]
            log: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            image_save_file: Optional[str]
            read_image: Optional[str]
            json_file: Optional[str]
            template_file: Optional[str]

        """Parse the arguments passed to the program."""
        args = super().parse_args()
        return _Args(
            mode=args.mode,
            log=args.log,
            image_save_file=args.image_save_file,
            read_image=args.read_image,
            json_file=args.json_file,
            template_file=args.template,
        )
