import logging
from pyfhirsdc.serializers.utils import get_resource_path, write_page_content
import json

logger = logging.getLogger("default")

def excel_to_json(worksheets, l2file):
    logger.info("converting excel to json.....")
    if len(worksheets) > 0:
        sheets = []
        for worksheet in worksheets:
            sheet_dict = {}
            worksheet_content = l2file.parse(worksheet)
            worksheet_content = worksheet_content[worksheet_content.columns.values].replace("\u200c", " ").replace("\u2265", " ").replace("\n", " ")
            worksheet = worksheet.replace("_", ".")
            worksheet_content = worksheet_content.fillna("BLANK")
            logger.info("creating data dictionary page {0}".format(worksheet.replace("\u2265", " ")))
            worksheet_content_json = worksheet_content.to_dict(orient="records")
            sheet_dict["sheet_name"] = worksheet
            sheet_dict["content"] = worksheet_content_json
            sheets.append(sheet_dict)

        json_file_path = get_resource_path("pagecontent", "l2.json")
        with open(json_file_path, 'w') as outfile:
            json.dump(sheets, outfile, indent = 4)
        l2file.close()