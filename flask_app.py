from flask import Flask, jsonify
from flask import make_response, jsonify
from flask_restful import Resource, Api, request, abort

from typing import NamedTuple, Optional
from persistence.inmate_dao import InmateDAO, QueryCondition
from persistence.data_models import *
from persistence.model import Model, model_from_dict, model_as_dict


app = Flask(__name__)
api = Api(app)
dao = InmateDAO()

API_OPTIONS = [
    {
        "resource": "/api/inmates",
        "endpoints": [
            "/api/inmates",
            "/api/inmates/jailed",
            "/api/inmates/released"
        ],
        "methods": ["GET"]
    },
    {
        "resource": "/api/search",
        "endpoints": [
            "/api/search",
            "/api/search/firstname/",
            "/api/search/lastname/"
        ],
        "methods": ["GET"]
    }
]


@app.errorhandler(404)
def not_found(e):
    message = jsonify("Invalid resource URI")
    return make_response(message, 404)

@api.resource("/api/", "/")
class ApiRoot(Resource):
    def options(self):
        return API_OPTIONS

@api.resource("/api/inmates/")
class InmatesRoot(Resource):
    def get(self):
        members = dao.get_all_members()
        return jsonify([e.as_dict() for e in members])

@api.resource("/api/inmates/jailed")
class JailedInmates(Resource):
    def get(self):
        current_inmates = dao.get_all_current_inmates()
        return jsonify([e.as_dict() for e in current_inmates])

@api.resource("/api/inmates/released")
class ReleasedInmates(Resource):
    def get(self):
        released_members = dao.get_all_released_members()
        return jsonify([e.as_dict() for e in released_members])

@Model
class SearchArgs(NamedTuple):
    attribute: str
    target: object
    condition: Optional[str] = "match_eq"

@api.resource("/api/inmates/search/")
class InmatesSearch(Resource):
    def get(self):
        if not request.is_json:
            abort(400, message="Body must contain json with `attribute` and `target.`")

        query = model_from_dict(SearchArgs, request.json)
        if query is None:
            abort(400, message="Body must contain json with `attribute` and `target.`")

        try:
            condition_func = QueryCondition.conditions[query.condition]
        except:
            abort(400, message=f"Bad request: `{query.condition}` is not a valid match condition.")
        
        
        condition = condition_func(query.target)
        attribute = query.attribute
        members = dao.get_members_by_attribute(attribute, condition)

        return jsonify({
            "query" : model_as_dict(query),
            "results" : [e.as_dict() for e in members]
        })

@api.resource("/api/inmates/search/lastname/<last_name>")
class InmatesSearchLastName(Resource):
    def get(self, last_name):
        members = dao.get_members_by_lastname(last_name)
        return jsonify([e.as_dict() for e in members])

@api.resource("/api/inmates/search/firstname/<first_name>")
class InmatesSearchFirstName(Resource):
    def get(self, first_name):
        members = dao.get_members_by_firstname(first_name)
        return jsonify([e.as_dict() for e in members])


if __name__ == "__main__":
    app.run(debug=False)
