import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

AWS_ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
AWS_SECRET = os.environ['AWS_SECRET']


def read_from_s3(bucket, filename, access_key=AWS_ACCESS_KEY, secret=AWS_SECRET):
    pth = f"s3://{bucket}/{filename}"
    print(pth)
    df = pd.read_csv(
        pth,
        storage_options={
            "key": access_key,
            "secret": secret
        }
    )

    return df

def get_dd():
    return read_from_s3('meta.idlewildtech.com', 'data/dd.csv').set_index('colname').to_dict()['coltype']

def get_df():
    df = read_from_s3('meta.idlewildtech.com', 'data/df_latest.csv')
    dd = get_dd()

    for c in df:
        if dd[c] == 'numeric':
            df[c] = pd.to_numeric(df[c], errors='coerce')

    return df

def get_df_for_download(file):
    if file == 'original':
        return read_from_s3('meta.idlewildtech.com', 'data/df_original.csv')
