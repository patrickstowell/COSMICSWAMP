from dash import Dash, dash_table

class dash_helper:
    def __init__(self):
        return
    
    def simple_pandas_table(self, rundata, id):
                
        runtable = dash_table.DataTable(rundata.to_dict('records'), 
                                                [{"name": i, "id": i} for i in rundata.columns], 
                                                page_action='none',
                                                id=id
                                                )
        return runtable
    
dash_tools = dash_helper()