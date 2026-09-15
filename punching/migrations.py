"""Compatibility for archived collections with vendor-specific adapter names.

The archived shape and the profile suffix identify the format. Derived actions
are still rebuilt and validated from the original records by the normal loader.
"""
from copy import deepcopy


def normalize_archive(payload):
    data=deepcopy(payload)
    prefixes=set()
    def discover(item):
        if isinstance(item,dict):
            adapter=item.get('adapter','')
            if isinstance(adapter,str) and adapter.partition('.')[2] in {'bar-joint/1','joint-frame/1','model-ref/1'}:
                prefix=adapter.partition('.')[0]
                if prefix!='Modelo':prefixes.add(prefix)
            for value in item.values():discover(value)
        elif isinstance(item,list):
            for value in item:discover(value)
    discover(data)
    # A collection containing tables only may have no candidate yet.
    if isinstance(data,dict):
        for name in data:
            if name.endswith('_tables') and name!='analysis_tables':prefixes.add(name[:-7].capitalize())
    def transform(item):
        if isinstance(item,list):return [transform(v) for v in item]
        if not isinstance(item,dict):return item
        result={}
        for name,value in item.items():
            new_name=name
            for prefix in prefixes:
                if name in {prefix.lower(),prefix.lower()+'_tables',prefix.lower()+'_nodes'}:
                    new_name='analysis'+name[len(prefix):]
            result[new_name]=transform(value)
        adapter=result.get('adapter','')
        if isinstance(adapter,str) and adapter.partition('.')[0] in prefixes:
            result['adapter']='Modelo.'+adapter.partition('.')[2]
        # These are explanatory adapter labels, not numeric source records.
        if 'method' in result and 'adapter' in result:
            for prefix in prefixes:result['method']=result['method'].replace(prefix,'Modelo')
        return result
    return transform(data)
