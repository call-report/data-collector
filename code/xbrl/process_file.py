import json
import io
import zipfile
from tqdm import tqdm
import re
from datetime import datetime
import xmltodict
from itertools import chain
import os
from hashlib import sha256
from uuid import uuid4
import hashlib
import time
import itertools
from zipfile import ZipFile

re_date = re.compile('[0-9]{4}\-[0-9]{2}\-[0-9]{2}')

def process_xbrl_file(file_name) -> str:

    raw_data = open(file_name,'rb').read()
    zip_io = io.BytesIO()
    zip_io.write(raw_data)
    zip_io.seek(0)
    zip_stream = ZipFile(zip_io)
    files = zip_stream.filelist
    files_list = list(files)

    tmp_file_name = '/tmp/' + str(uuid4())

    # write an opening bracket to the temp_file_name
    with open(tmp_file_name, 'w') as f:
        f.write('[')

    all_data = []
    for i, file in tqdm(enumerate(files_list)):
        if file.filename.endswith('.xml'):
            if 'RSSD' in file.filename:
                data = zip_stream.open(file).read()
                try:
                    all_data.append(process_xml(data, tmp_file_name))
                
                    # is this the last file?
                    if file == len(files_list)-1:
                        # write a closing bracket to the temp_file_name
                        with open(tmp_file_name, 'a') as f:
                            f.write(']')
                    else:
                        # write a comma to the temp_file_name
                        with open(tmp_file_name, 'a') as f:
                            f.write(',')

                except:
                    print(f"Error processing {file}")
                    continue

    # return the text contained within the tmp_file_name
    ret_str = open(tmp_file_name, 'r').read()
    os.remove(tmp_file_name)
    return ret_str

def process_date_tuple(dt):
    return f"{str(dt[0]).zfill(4)}-{str(dt[1]).zfill(2)}-{str(dt[2]).zfill(2)}"

def return_dt(file_name):
    return datetime.strptime(re.findall('0{1}[0-9]{7}', file_name)[0],'%m%d%Y').strftime('%Y-%m-%d')


def dict_to_array(adict, col):
    return [r[col] for r in adict]

def process_xml(data, tmp_file_name):

    ## embedding for use in ray
    def process_xbrl_item(name, items):
        # incoming is a data dictionary
        results = []
        if type(items) != list:
            items = [items]
        for j,item in enumerate(items):
            context = item.get('@contextRef')
            unit_type = item.get('@unitRef')
            value = item.get('#text')
            mdrm = name.replace("cc:","").replace("uc:","")
            rssd = context.split('_')[1]
            #date = int(context.split('_')[2].replace("-",''))

            quarter = re_date.findall(context)[0]

            data_type = None

            if unit_type == 'USD':
                value = int(value)/1000
                data_type = 'int'
            elif unit_type == 'PURE':
                value = float(value)
                data_type = 'float'
            elif unit_type == 'NON-MONETARY':
                value = float(value)
                data_type = 'float'
            elif value == 'true':
                value = True
                data_type = 'bool'
            elif value == 'false':
                value = False
                data_type = 'bool'
            else:
                data_type = 'str'                

            results.append({'mdrm':mdrm, 'rssd':rssd, 'value':value, 'data_type':data_type, 'quarter':quarter})

        return results

    ## end embeddint for ray

    #data = zipfile_stream.open(first_file).read()
    dict_data = xmltodict.parse(data.decode('utf-8'))['xbrl']
    # only include ubpr data
    keys_to_parse = list(filter(lambda x: 'cc:' in x, dict_data.keys())) + list(filter(lambda x: 'uc:' in x, dict_data.keys()))
    parsed_data = list(chain.from_iterable(filter(None,list(map(lambda x: process_xbrl_item(x, dict_data[x]),keys_to_parse)))))
    ret_data = []
    for row in parsed_data:
        new_dict = {}
        new_dict.update({'mdrm':row['mdrm']})
        new_dict.update({'rssd':row['rssd']})
        new_dict.update({'quarter':row['quarter']})
        if row['data_type'] == 'int':
            new_dict.update({'int_data':int(row['value'])})
            new_dict.update({'data_type':row['data_type']})

        elif row['data_type'] == 'float':
            new_dict.update({'float_data':row['value']})
            new_dict.update({'data_type':row['data_type']})

        elif row['data_type'] == 'str':
            new_dict.update({'str_data':row['value']})
            new_dict.update({'data_type':row['data_type']})

        elif row['data_type'] == 'float':
            new_dict.update({'float_data':row['value']})
            new_dict.update({'data_type':row['data_type']})

        elif row['data_type'] == 'bool':
            new_dict.update({'bool_data':row['value']})
            new_dict.update({'data_type':row['data_type']})

        ret_data.append(new_dict)

    
    # write the data to the temp_file_name
    with open(tmp_file_name, 'a') as f:
        f.write(json.dumps(ret_data))

    return

