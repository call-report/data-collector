import json
import io
import zipfile
from tqdm import tqdm
import re
import xmltodict
from itertools import chain
import os
from uuid import uuid4

re_date = re.compile('[0-9]{4}\-[0-9]{2}\-[0-9]{2}')

re_date = re.compile('[0-9]{4}\-[0-9]{2}\-[0-9]{2}')

def process_xbrl_file(file_name) -> str:
    with open(file_name, 'rb') as file:
        raw_data = file.read()

    zip_io = io.BytesIO(raw_data)
    zip_stream = zipfile.ZipFile(zip_io)
    files_list = [f for f in zip_stream.filelist if f.filename.endswith('.xml') and 'RSSD' in f.filename]

    tmp_file_name = '/tmp/' + str(uuid4())

    # Write an opening bracket to the temp_file_name
    with open(tmp_file_name, 'w') as f:
        f.write('[\n')

    for i, file in tqdm(enumerate(files_list), total=len(files_list)):
        if 'RSSD' in file.filename:
            data = zip_stream.open(file).read()
            try:
                processed_data = process_xml(data)
                with open(tmp_file_name, 'a') as f:
                    json.dump(processed_data, f, indent=4)
                    if i < len(files_list) - 1:
                        f.write(',\n')
                    else:
                        f.write('\n')
            except Exception as e:
                print(f"Error processing {file.filename}: {e}")

    # Write a closing bracket to the temp_file_name
    with open(tmp_file_name, 'a') as f:
        f.write(']')

    # Read the complete JSON data
    with open(tmp_file_name, 'r') as f:
        ret_str = f.read()

    os.remove(tmp_file_name)
    return ret_str

def process_xml(data):
    dict_data = xmltodict.parse(data.decode('utf-8'))['xbrl']
    keys_to_parse = list(filter(lambda x: 'cc:' in x, dict_data.keys())) + list(filter(lambda x: 'uc:' in x, dict_data.keys()))
    parsed_data = list(chain.from_iterable(filter(None, (process_xbrl_item(x, dict_data[x]) for x in keys_to_parse))))
    
    ret_data = []
    for row in parsed_data:
        new_dict = {
            'mdrm': row['mdrm'],
            'rssd': row['rssd'],
            'quarter': row['quarter'],
            f"{row['data_type']}_data": row['value']
        }
        ret_data.append(new_dict)
    
    return ret_data

def process_xbrl_item(name, items):
    if not isinstance(items, list):
        items = [items]

    results = []
    for item in items:
        context = item.get('@contextRef')
        unit_type = item.get('@unitRef')
        value = item.get('#text')
        mdrm = name.replace("cc:", "").replace("uc:", "")
        rssd = context.split('_')[1]
        quarter = re_date.findall(context)[0]

        data_type = 'str'  # Default data type
        if unit_type == 'USD':
            value = int(value) / 1000
            data_type = 'int'
        elif unit_type in ['PURE', 'NON-MONETARY']:
            value = float(value)
            data_type = 'float'
        elif value in ['true', 'false']:
            value = value == 'true'
            data_type = 'bool'

        results.append({'mdrm': mdrm, 'rssd': rssd, 'value': value, 'data_type': data_type, 'quarter': quarter})

    return results


