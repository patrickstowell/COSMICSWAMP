from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

def CustomGridLayout( id, children, layout, height ):
        
    # Setup is a list of rows with associated columns.
    # First get unique rows.
    rows = {}
    maxy = 0
    for c in children:
        
        idset = None
        for j in layout:
            if j["i"] == c.id:
                idset = c.id
                layoutset = j
        
        y = int(layoutset["y"])
        if y not in rows: rows[y] = []
        rows[y].append( [layoutset, c] )
        if y > maxy: maxy = y
       
    for key in rows:
        print(key)
    allrows = []
    
    
    for y in range(maxy+1):
        
        if y in rows:
            print("VALID ENTRTY", y)
                        
            items = []
            maxh = 0
            for entry in rows[y]:
                
                layitem = entry[0]
                divitem = entry[1]
                
                w = layitem["w"]
                h = layitem["h"]
                if h > maxh: maxh = h
                print("W", w)
                items.append( html.Div(divitem,style={"height": f"{h*700/10}px", "width": f"{w*1200/20}px"}, className="customgrid-col"))
                
            allrows.append(html.Div( items, className="customgrid-row" ))
            
            
    
        
            
    print("HTML LEN",len(allrows))
    return html.Div(allrows, id=id)