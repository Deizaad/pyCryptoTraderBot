import os
import pytz
from datetime import date, datetime
from persiantools.jdatetime import JalaliDate    # type: ignore
import logging

def initialize_logger():
    file_name = str(datetime.now(pytz.timezone('Asia/Tehran')).strftime("%H-00")) + '.log'

    folder_name = './Logs/'
    month_folder_name = str(date.today().strftime("%B_%Y-%m")) \
                        + str(JalaliDate.today().strftime("(%B_%Y-%m)/"))
    
    day_folder_name = str(date.today().strftime("%A_%B_%d")) \
                      + str(JalaliDate.today().strftime("(%A_%d_%B)/"))
    path = str(folder_name+month_folder_name+day_folder_name)
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == 17:
            print(f'Attempt to create Logs directory {path}: It already exsist!')
        else:
            print(f'Attempt to create Logs directory: error accured: {err}')

    logging.basicConfig(
        filename = path+file_name,
        filemode='w',
        format = "%(levelname)s from \"%(funcName)s\" in \"%(filename)s\" at %(asctime)s:\n    %(message)s\n",
        level=logging.DEBUG
    )

    logging.getLogger().addHandler(logging.StreamHandler())

    logging.info('Logger has been initialized.')