import io
import os
import logging

from google.cloud import vision

logger = logging.Logger(__name__)


class TicketAnalyzer:
    def __init__(self, input_file_path, output_file_path):
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path

    def process(self):
        client = vision.ImageAnnotatorClient()
        logger.info(f"Processing {self.input_file_path}")
        with io.open(self.input_file_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.text_detection(image=image)
        texts = response.text_annotations

        output = ""

        for text in texts:
            output += '\n"{}"'.format(text.description)

            vertices = (['({},{})'.format(vertex.x, vertex.y)
                         for vertex in text.bounding_poly.vertices])

        with open(self.output_file_path, 'w') as text_file:
            logger.info(
                f"Saving the output file to {self.output_file_path}")
            text_file.write(output)

        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))
