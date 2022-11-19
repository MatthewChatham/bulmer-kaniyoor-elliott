import psycopg2
import psycopg2.extras as extras

import pandas as pd

import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ['DATABASE_URL']

def get_conn():
    return psycopg2.connect(**psycopg2.extensions.parse_dsn(DATABASE_URL))

def get_dd():
    conn = get_conn()
    
    with conn, conn.cursor() as cur:
            cur.execute('select * from dd;')
            dd = pd.DataFrame(cur.fetchall(), columns=['colname', 'coltype'])
            dd = {r['colname']:r['coltype'] for i,r in dd.iterrows()}
            
    conn.close()
    
    return dd

def get_df():
    conn = get_conn()
    
    with conn, conn.cursor() as cur:
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
        
    conn.close()

    return df

def update_database(df, dd):
    """
    
    Given a pandas DataFrame and a dd representing 
    column types, load/update the database.
    
    """
    
    # fail if not all columns have types
    assert set(df.columns).issubset(set(dd.keys()))
    
    conn = get_conn()
    
    with conn, conn.cursor() as cur:

        print('dropping tables')
        # drop tables
        for table_name in ['df', 'dd']:
            cur.execute(f"DROP TABLE IF EXISTS {table_name};")

        print('recreating dd')
        # create and insert into dd
        cur.execute("""
            CREATE TABLE dd(
                colname text PRIMARY KEY,
                coltype text NOT NULL
            );
        """)
        print('inserting into dd')
        qstring = "INSERT INTO dd VALUES %s"
        extras.execute_values(cur, qstring, [(k,v) for k,v in dd.items()])

        print('recreating df')
        # create df
        colnames = df.columns
        qstring = """CREATE TABLE df("""
        to_join = []
        for c in colnames:
            to_join.append(f""""{c}" {'numeric' if dd[c] == 'numeric' else 'text'}""")
        qstring += ',\n'.join(to_join)
        qstring += ");"
        cur.execute(qstring)

        print('inserting into df')
        # insert into df
        qstring = "INSERT INTO df VALUES %s"
        records = []
        for i,r in df.iterrows():
            records.append(tuple(r.values))
        extras.execute_values(cur, qstring, records)
        
    conn.close()
    