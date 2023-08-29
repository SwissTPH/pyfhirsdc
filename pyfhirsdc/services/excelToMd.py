import logging
from py_markdown_table.markdown_table import markdown_table
from pyfhirsdc.serializers.utils import get_page_content_path, write_page_content
import json

logger = logging.getLogger("default")

def generate_page_from_excel(data_dictionary_worksheets, data_dictionary_file, outputFile: str, title="UNTITLED", header=3):
    logger.info("processing data dictionary")
    if len(data_dictionary_worksheets) > 0:
        fileContent = []
        data_dictionary_file_content = ""
        for worksheet in data_dictionary_worksheets:
            worksheet_content = data_dictionary_file.parse(worksheet, header = header)
            worksheet_content = worksheet_content[worksheet_content.columns.values].replace("\u200c", " ").replace("\u2265", " ").replace("\n", " ")
            worksheet = worksheet.replace("_", ".")
            logger.info("creating data dictionary page {0}".format(worksheet.replace("\u2265", " ")))

            worksheet_content_json = worksheet_content.to_dict(orient="records")
            new_line = "### " + worksheet + "\n\n"
            markdown_woksheet_content = markdown_table(worksheet_content_json).set_params(row_sep="markdown").get_markdown()
            markdown_woksheet_content += "\n {: .dataframe.table.table-striped.table-bordered}"
            
            new_line += markdown_woksheet_content.replace("```", "") + "\n\n"
            data_dictionary_file_content += new_line
        data_dictionary_file_path = get_page_content_path("/", outputFile)
        write_page_content(data_dictionary_file_path, title, data_dictionary_file_content)
        data_dictionary_file.close()
        