from dash import html, dcc
import dash_bootstrap_components as dbc

def generate_filter_control(c, df, dd, ctrl_value=None, null_value=None):
    """
    Given a column name `c`,
    generate an appropriate filter control based
    on the column type and values.
    """
        
    control = None
    res = [
        html.H6(c),
        None        
    ]
    
    if dd[c] == 'numeric':
        
        rng = [
            df[c].astype(float).min(),
            df[c].astype(float).max()
        ]
        
        ctrl_value = ctrl_value if ctrl_value else rng
        
        control = dcc.RangeSlider(
            *rng,
            value=ctrl_value,
            id={'type': 'filter-control', 'column': c}
        )
    else:
        
        ctrl_value = ctrl_value if ctrl_value else df[c].unique()
        
        control = dcc.Dropdown(
            df[c].dropna().unique(),
            value=ctrl_value,
            multi=True, 
            placeholder=c, 
            id={'type': 'filter-control', 'column': c}
        )
    
    null_value = null_value if null_value is not None else ['Include null']
    
    res[1] = dbc.Row([
        dbc.Col(control, width=8),
        dbc.Col(dcc.Checklist(
            ['Include null'], 
            null_value,
            inputStyle={'margin-right': '5px'},
            id={'type': 'filter-null', 'column': c}
        ), width=4)
    ])
        
    # print('Appending to children:')
    # print(res)
        
    return html.Div(res, style={'margin-top': '1rem'})


def get_filter_mask(
    legend, 
    dope, 
    df,
    dd,
    ctrl_values, 
    ctrl_idx, 
    null_values,
    apply_filters
):
    """
    Given a list of `filters`, the `legend` and `dope` controls,
    and a pandas `df`, build a mask.
    """
    
    ctrl_cols = [i['column'] for i in ctrl_idx]
    
    mask = df['Category'].isin(legend) & \
    df['Doped or Acid Exposure (Yes/ No)'].isin(dope)
    
    if not ctrl_values or not apply_filters:
        return mask
    
    for i,c in enumerate(ctrl_cols):   
        if dd[c] == 'numeric':
            m = df[c].between(*ctrl_values[i])
            if null_values[i]:
                m = m | df[c].isnull()
        else:
            m = df[c].isin(ctrl_values[i])
            if null_values[i]:
                m = m | df[c].isnull()
        
        mask = mask & m
        
    return mask