import logging
import pandas as pd 
from pathlib import Path

from pyfhirsdc.config import get_dict_df
from pyfhirsdc.converters.changes import convert_df_to_changes
from pyfhirsdc.serializers.utils import get_page_content_path, write_page_content

logger = logging.getLogger("default")


def generateChagnes():
    logger.info("processing changes................")

    changes = convert_df_to_changes().iloc[1:]

    if len(changes.index > 0):
        fileContent = []
        for row in changes.itertuples():
            logger.info("Saving changes for %s", row[1])
            new_line = "##" + row[1] + " " + row[2]
            new_line += "\n\n" + row[3]
            fileContent.append(new_line)
        
        changes_file_path = get_page_content_path("/", "changes.md")
        write_page_content(changes_file_path, "Changes", "\n".join(fileContent))