import numpy as np
import pandas as pd

def clean(df, numeric_cols):
    """
    Given a DataFrame, coerce numeric_cols to numeric
    and drop unnamed/duped columns.
    """
    
    df = df.copy()
    dropped_cols = list()
    
    # -----------------------STRIP WHITESPACE FROM VALUES ----------------------------
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    
    # ----------------------- STANDARDIZE NANS ---------------------------------------
    for c in df.columns:
        mask = df[c].astype(str).str.lower().str.replace('\s+', '', regex=True).str.contains('notreported')
        df.loc[mask, c] = np.NaN
    
    # ----------------------DROP UNNAMED AND DUPED COLUMNS ---------------------------
    drop_cols = [c for c in df.columns if 'Unnamed' in c or c.endswith('.1')]
    df = df.drop(drop_cols, axis=1)
    
    # -----------------------CONVERT NUMERIC COLS TO FLOAT ---------------------------
    for c in df.columns:
        if c in numeric_cols:
            df[c] = pd.to_numeric(
                df[c],
                errors='coerce' # silently coerce non-numeric values to NaN
            )
    


    return {'data': df, 'dropped': drop_cols}

def get_data_dict(cur):
    
    cur.execute('select * from data_dict;')
    data_dict = pd.DataFrame(cur.fetchall(), columns=['colname', 'coltype'])
    
    return data_dict