def convert_date_format(date_string):
    date_string = date_string.split('/')
    new_date_string = date_string[2].zfill(2) + date_string[0].zfill(2) + date_string[1].zfill(2)
    return new_date_string


def convert_from_yyyymmdd(date_string):
    new_date_string = date_string[4:6] + "/" + date_string[6:8] + "/" +date_string[0:4]
    return new_date_string