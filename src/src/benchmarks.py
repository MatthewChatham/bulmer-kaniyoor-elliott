BENCHMARK_COLORS = {
        'Copper': '#B87333',
        'Iron': '#a19d94',
        'Steel': 'white',
        'SCG': 'black'
    }

def compute_benchmarks(df, y):
    res = {
        'Copper': None,
        'Iron': None,
        'SCG': None,
        'Steel': None
    }
    
    res['Copper'] = df.loc[df.Notes == 'Copper', y].mean()
    res['Iron'] = df.loc[df.Notes == 'Iron', y].mean()
    mask = df.Notes == 'Single Crystal Graphite'
    res['SCG'] = df.loc[mask, y].mean()
    
    mask = df.Notes.fillna('').str.contains('steel', case=False)
    res['Steel'] = df.loc[mask, y].mean()
    
    return res

def compute_benchmarks_g2(df, x, y):
    # todo: add aluminum for both benchmarks
    res = {
        'Copper': [],
        'Iron': [],
        'SCG': [],
        'Steel': [],
    }
    
    # Compute X
    res['Copper'].append(df.loc[df.Notes == 'Copper', x].mean())
    res['Iron'].append(df.loc[df.Notes == 'Iron', x].mean())
    
    mask = df.Notes == 'Single Crystal Graphite'
    res['SCG'].append(df.loc[mask, x].mean())
    
    mask = df.Notes.fillna('').str.contains('steel', case=False)
    res['Steel'].append(df.loc[mask, x].mean())
    
    # Compute Y
    res['Copper'].append(df.loc[df.Notes == 'Copper', y].mean())
    res['Iron'].append(df.loc[df.Notes == 'Iron', y].mean())
    
    mask = df.Notes == 'Single Crystal Graphite'
    res['SCG'].append(df.loc[mask, y].mean())
    
    mask = df.Notes.fillna('').str.contains('steel', case=False)
    res['Steel'].append(df.loc[mask, y].mean())
    
    return res