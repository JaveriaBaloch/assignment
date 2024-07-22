import xmltodict
from flask import abort

class XMLHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_xml_to_dict(self):
        try:
            with open(self.file_path, 'r') as file:
                xml_content = file.read()
            return xmltodict.parse(xml_content)
        except FileNotFoundError:
            abort(404, description="File not found")
        except Exception as e:
            abort(500, description=str(e))
