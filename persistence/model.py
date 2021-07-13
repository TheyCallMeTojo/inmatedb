from functools import partial
from typing import NamedTuple
import inspect
import json


def has_method(obj, name):
    if hasattr(obj, name):
        attribute = getattr(obj, name)
        return inspect.ismethod(attribute)
    
    return False

def model_from_dict(model: NamedTuple, values_dict: dict):
    input_keys = set(values_dict.keys())
    unexpected_keys = input_keys - set(model._fields)
    
    filtered_values = {
        key: value for (key, value) in values_dict.items() 
        if key not in unexpected_keys
    }
    filtered_keys = set(filtered_values.keys())

    required_model_keys = set(model._fields) - set(model._field_defaults)
    required_keys_met = set.issubset(required_model_keys, filtered_keys)

    if not required_keys_met:
        return None
    
    return model(**filtered_values)

def model_as_dict(model: NamedTuple):
    model_dict = dict()

    field_names = model._fields
    for field_idx, field_name in enumerate(field_names):
        attribute = model[field_idx]
        
        if has_method(attribute, "as_dict"):
            attr_dict = attribute.as_dict()
            model_dict[field_name] = attr_dict
        else:
            model_dict[field_name] = attribute

    return model_dict

def model_as_json(model: NamedTuple):
    model_dict = model_as_dict(model)
    model_json = json.dumps(model_dict, indent=2)
    return model_json

def Model(model: NamedTuple):
    '''Decorator to add extra functionality to NamedTuples'''

    model.as_dict = model_as_dict
    model.as_json = model_as_json
    model.__str__ = model_as_json
    return model

