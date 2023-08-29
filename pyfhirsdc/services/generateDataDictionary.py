import logging
from py_markdown_table.markdown_table import markdown_table
from pyfhirsdc.serializers.utils import get_page_content_path, write_page_content
import json

logger = logging.getLogger("default")

def generate_data_dictionary_page(data_dictionary_worksheets, data_dictionary_file):
    logger.info("processing data dictionary")
    if len(data_dictionary_worksheets) > 0:
        fileContent = []
        data_dictionary_file_content = ""
        for worksheet in data_dictionary_worksheets:
            worksheet_content = data_dictionary_file.parse(worksheet, header=3)
            worksheet_content = worksheet_content[worksheet_content.columns.values].replace("\u200c", " ").replace("\u2265", " ").replace("\n", " ")
            worksheet = worksheet.replace("_", ".")
            logger.info("creating data dictionary page {0}".format(worksheet.replace("\u2265", " ")))

            worksheet_content_json = worksheet_content.to_dict(orient="records")
            new_line = "### " + worksheet + "\n\n"
            markdown_woksheet_content = markdown_table(worksheet_content_json).set_params(row_sep="markdown").get_markdown()
            
            new_line += markdown_woksheet_content.replace("```", "") + "\n\n"
            data_dictionary_file_content += new_line
        data_dictionary_file_path = get_page_content_path("/", "dictionary.md")
        write_page_content(data_dictionary_file_path, "Data Dictionary", data_dictionary_file_content)
        data_dictionary_file.close()
        