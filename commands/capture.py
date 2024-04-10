import cv2 as cv
from logger import Logger
import neoapi

# neoapi = any

# # ? This is a workaround for not installing the neoapi package on Windows, since it
# # ? will not be used on Windows.
# if not os.name == "nt":


class Capture:
    @classmethod
    def run(cls, image_save_file: str):
        Logger.debug("Running capture command.")

        if not image_save_file.endswith(".png"):
            # ! ERROR CODE 4
            Logger.err_exit(f"{image_save_file} is not PNG.", code=4)
        try:
            camera = neoapi.Cam()
            camera.Connect()

            Logger.debug("Connected to the camera.")
            image = None
            for _ in range(200):
                img = camera.GetImage()
                if not img.IsEmpty():
                    Logger.debug("Image captured.")
                    image = img.GetNPArray()
                    break

            if image is None:
                raise Exception("No image found.")

            cv.imwrite(image_save_file, image)

        except (neoapi.NeoException, Exception) as err:
            Logger.debug(f"Exception: {err}")
            # ! ERROR CODE 13
            Logger.err_exit("CAMERA | Unable to capture image.", code=13)

        Logger.debug("Image written to disk.")
