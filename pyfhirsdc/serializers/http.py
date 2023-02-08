import json
import logging

import requests
from requests_toolbelt.multipart import decoder

from pyfhirsdc.serializers.json import read_file

logger = logging.getLogger("default")


def put_files(file_path, url):
    logger.info("Sending the file {0}".format(url))
    buffer= read_file(file_path, type = "str")
    headers_map = {'Content-type': 'application/json'}
    response = requests.put(url, data = buffer.encode(), headers = headers_map)
    if response.status_code == 200 or response.status_code == 201:
        logger.debug(response.status_code)
    else:
        logger.error(str(response.status_code))
        logger.debug(response.text)
        
def post_files(file_path, url):
    logger.debug("Sending the file {0}".format(url))
    buffer= read_file(file_path, type = "str")
    headers_map = {'Content-type': 'application/json'}
    response = requests.post(url, data = buffer.encode(), headers = headers_map)
    if response.status_code == 200 or response.status_code == 201:
        logger.debug(response.status_code)
    else:
        logger.error(str(response.status_code))
        logger.debug(response.text)

def post_multipart(list, url):
    logger.debug("Sending the multipart to {0} and pasing multipart answer".format(url))
    for id, part in list.items():
        logger.debug(id)
    response = requests.post(url, files = list,headers={'Cache-Control': 'no-cache'})
    if response.status_code == 200 or response.status_code == 201 :
        logger.debug(response.status_code)
        multipart_data = decoder.MultipartDecoder.from_response(response)
        return multipart_data
    else:
        logger.error(str(response.status_code))
        logger.debug(response.text)
        
online = None

def check_internet():
    global online
    if online is None:
        url = "http://www.google.com"
        timeout = 5
        try:
            request = requests.get(url, timeout=timeout)
            online = True
        except (requests.ConnectionError, requests.Timeout) as exception:
            logger.warning("No internet connection.")
            online = False
    return online
