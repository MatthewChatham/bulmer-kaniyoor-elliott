import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras as extras

MARKERS = {
    'Aligned Few-wall CNTs': {
        'marker_symbol': 'diamond',
        'marker_color': '#305ba9'
    },
    'Aligned Multiwall CNTs': {
        'marker_symbol': 'triangle-up',
        'marker_color': '#d12232'
    },
    'Amorphous carbon': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Carbon Fiber': {
        'marker_symbol': 'square-open',
        'marker_color': 'black'
    },
    'Conductive Polymer': {
        'marker_symbol': 'square',
        'marker_color': '#cc3b8c'
    },
    'Diamond': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'GIC': {
        'marker_symbol': 'square',
        'marker_color': 'black'
    },
    'Glassy Carbon': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Graphene Nanoribbon': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Individual Bundle': {
        'marker_symbol': 'cross',
        'marker_color': '#305ba9'
    },
    'Individual FWCNT': {
        'marker_symbol': 'x',
        'marker_color': '#305ba9'
        
    },
    'Individual Multiwall CNTs': {
        'marker_symbol': 'star',
        'marker_color': '#d12232'
    },
    'Metal': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Metal CNT Composite': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Mott minimum conductivity': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Paper': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Single crystal graphite': {
        'marker_symbol': 'square-open',
        'marker_color': 'black'
    },
    'Superconductor': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Synthetic fiber': {
        'marker_symbol': 'circle',
        'marker_color': 'gray'
    },
    'Unaligned Few-wall CNTs': {
        'marker_symbol': 'circle',
        'marker_color': '#61b84e'
    },
    'Unaligned multiwall CNTs': {
        'marker_symbol': 'square',
        'marker_color': '#ee9752'
    }
}

CATEGORY_MAPPER = {
	'Aligned Multiwall CNTs': 'Aligned MWCNT',
	'Aligned Few-wall CNTs': 'Aligned FWCNT',
	'Unaligned Few-wall CNTs': 'Unaligned FWCNT',
	'GIC': 'Other Carbons',
	'Individual Multiwall CNTs': 'Individual Structures',
	'Conductive Polymer': 'Other Carbons',
	'Carbon Fiber': 'Other Carbons',
	'Individual FWCNT': 'Individual Structures',
	'Metal': 'Other',
	'Unaligned multiwall CNTs': 'Unaligned MWCNT',
	'Individual Bundle': 'Individual Structures',
	'Metal CNT Composite': 'Other',
	'Single crystal graphite': 'Individual Structures',
	'Synthetic fiber': 'Other',
	'Graphene Nanoribbon': 'Other',
	'Paper': 'Other',
	'Amorphous carbon': 'Other',
	'Glassy Carbon': 'Other',
	'Mott minimum conductivity': 'Other',
	'Superconductor': 'Other',
	'Diamond': 'Other',
}

def get_conn():
    
    pth = "/Users/mac/Documents/Consulting/bulmer"\
    "/meta_analysis_app/meta_analysis_app/.env"
    
    with open(pth, 'r') as f:
        line1 = f.read().split('\n')[0]
        DATABASE_URL = line1.split('=')[1]
    
    conn = psycopg2.connect(**psycopg2.extensions.parse_dsn(DATABASE_URL))
    
    return conn

def clean(df, numeric_cols):
    """
    Given a DataFrame, coerce numeric_cols to numeric
    and drop unnamed/duped columns.
    """
    
    df = df.copy()
    dropped_cols = list()
    
    # -----------------------STRIP WHITESPACE FROM VALUES ---------------------
    print('strip whitespace')
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    
    # ----------------------- STANDARDIZE NANS --------------------------------
    print('standardize nans')
    for c in df.columns:
        mask = (
            df[c].astype(str).str.lower()
            .str.replace('\s+', '', regex=True)
            .str.contains('notreported|nan')
        )
        df.loc[mask, c] = np.NaN
    
    # ----------------------DROP UNNAMED AND DUPED COLUMNS --------------------
    print('drop unnamed/dupes')
    drop_cols = [c for c in df.columns if 'Unnamed' in c or c.endswith('.1')]
    df = df.drop(drop_cols, axis=1)
    
    # -----------------------CONVERT NUMERIC COLS TO FLOAT --------------------
    print('coerce to float')
    for c in df.columns:
        print(f'\tcoercing {c}')
        if c in numeric_cols:
            df[c] = pd.to_numeric(
                df[c],
                errors='coerce' # silently coerce non-numeric values to NaN
            )
    
    return {'data': df, 'dropped': drop_cols}

def get_dd(cur):
    
    cur.execute('select * from dd;')
    dd = pd.DataFrame(cur.fetchall(), columns=['colname', 'coltype'])
       
    dd = {r['colname']:r['coltype'] for i,r in dd.iterrows()}
    
    return dd

def get_df(cur):
    
    # get df column names
    cur.execute("""
    SELECT column_name
      FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name   = 'df'
         ;
    """)
    cols = [x[0] for x in cur.fetchall()]
    
    cur.execute('select * from df;')
    df = pd.DataFrame(cur.fetchall(), columns=cols)

    return df

def update_database(cur, df, dd):
    """
    
    Given a pandas DataFrame and a dd representing 
    column types, load/update the database.
    
    """
    
    # fail if not all columns have types
    assert set(df.columns).issubset(set(dd.keys()))
        
    # drop tables
    print('dropping tables')
    for table_name in ['df', 'dd']:
        cur.execute(f"DROP TABLE IF EXISTS {table_name};")
        # print(conn.notices[-1])
        

    # create and insert into dd
    print('creating dd')
    cur.execute("""
        CREATE TABLE dd(
            colname text PRIMARY KEY,
            coltype text NOT NULL
        );
    """)
    qstring = "INSERT INTO dd VALUES %s"
    print('inserting into dd')
    extras.execute_values(cur, qstring, [(k,v) for k,v in dd.items()])
    
    # create df
    print('creating df')
    colnames = df.columns
    qstring = """CREATE TABLE df("""
    to_join = []
    for c in colnames:
        to_join.append(f""""{c}" {'numeric' if dd[c] == 'numeric' else 'text'}""")
    qstring += ',\n'.join(to_join)
    qstring += ");"
    cur.execute(qstring)
    
    # insert into df
    print('inserting into df')
    qstring = "INSERT INTO df VALUES %s"
    records = []
    for i,r in df.iterrows():
        records.append(tuple(r.values))
    extras.execute_values(cur, qstring, records)