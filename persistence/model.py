from typing import NamedTuple
import inspect
import json


def has_method(obj, name):
    if hasattr(obj, name):
        attribute = getattr(obj, name)
        return inspect.ismethod(attribute)
    
    return False

def Model(model: NamedTuple):
    '''Decorator to add extra functionality to NamedTuples'''

    def as_dict(model: NamedTuple):
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

    def as_json(model: NamedTuple):
        model_dict = as_dict(model)
        model_json = json.dumps(model_dict, indent=2)
        return model_json
    
    model.as_dict = as_dict
    model.as_json = as_json
    model.__str__ = as_json
    return model
