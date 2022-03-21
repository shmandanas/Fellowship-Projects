import requests
import pandas as pd
import datetime
import arcpy
import os

#ingestion script adapted from https://github.com/movebank/movebank-api-doc/blob/master/mb_Meschenmoser.py
def scriptTool(Output_File_Name):
    username = '<AGOL USERNAME>'
    password = '<AGOL PASSWORD>'

    #movebank study ID
    studyID = <MOVEBANK STUDY ID>

    #time window from which to pull data
    now = datetime.datetime.now()
    then = now - datetime.timedelta(hours = 6)
    end_time = now.strftime("%Y%m%d%H%M%S000")
    start_time = then.strftime("%Y%m%d%H%M%S000")

    IDs2Names = {
        '<Movebank ID Number>': '<Bird Name>',

    }
    
    do_it = DataToCSV(studyID, start_time, end_time, IDs2Names, Output_File_Name)
    return(do_it)


def callMovebankAPI(params):
    # Requests Movebank API with ((param1, value1), (param2, value2),).
    # Assumes the environment variables 'mbus' (Movebank user name) and 'mbpw' (Movebank password).
    # Returns the API response as plain text.

    response = requests.get('https://www.movebank.org/movebank/service/direct-read', params=params, auth=('<MOVEBANK USERNAME>','<MOVEBANK PASSWORD>'))
    print("Request " + response.url)
    if response.status_code == 200:  # successful request
        if 'License Terms:' in str(response.content):
            # only the license terms are returned, hash and append them in a subsequent request.
            # See also
            # https://github.com/movebank/movebank-api-doc/blob/master/movebank-api.md#read-and-accept-license-terms-using-curl
            print("Has license terms")
            hash = hashlib.md5(response.content).hexdigest()
            params = params + (('license-md5', hash),)
            # also attach previous cookie:
            response = requests.get('https://www.movebank.org/movebank/service/direct-read', params=params,
                                    cookies=response.cookies, auth=('<MOVEBANK USERNAME>','<MOVEBANK PASSWORD>'))
            if response.status_code == 403:  # incorrect hash
                print("Incorrect hash")
                return ''
        return response.content.decode('utf-8')
    print(str(response.content))
    return ''

def DataToCSV(study_id, start_date,end_date, IDs2Names,Output_File_Name):
    #gets the data from movebank
    parameters = (('entity_type','event'),('study_id', study_id),('timestamp_start',start_date),('timestamp_end',end_date),('attributes','all'))
    output = callMovebankAPI(parameters)
    
    #puts data into a usable dataframe
    rows = output.splitlines()
    table = pd.DataFrame(rows)
    table = pd.DataFrame(table[0].str.split(',').tolist())
    heads = table.iloc[0]
    table = table[1:]
    table.columns = heads
    
    #change data type columns to numbers and dates
    #note: bird IDs not converted to numbers bc IDs are larger than 64 bit numbers
    floats = ['location_lat','location_long','tag_id','study_id',
             'sensor_type_id','gps_fix_type','gps_hdop','ground_speed',
             'heading','height_above_msl','tag_voltage','event_id']
    for f in floats:
        convert_dict = {f:float}
        table = table.astype(convert_dict)
    
    #remove "" from bird ID column, uses dictionary to add names to the table
    table.iloc[:,6] = table.iloc[:,6].str.replace('"','')
    table['Name'] = table['tag_local_identifier'].map(IDs2Names)
    
    #remove rows with lat/long of 0.0
    table = table.drop(table[(table['location_lat'] == 0.0) & (table['location_long'] == 0.0)].index)
    
    #export the table to CSV
    table.to_csv(Output_File_Name)
    
    

if __name__ == '__main__':
    # ScriptTool parameters
    Output_File_Name = arcpy.GetParameterAsText(0)
    
    running = scriptTool(Output_File_Name)