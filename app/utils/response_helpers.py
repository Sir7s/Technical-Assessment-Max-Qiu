from flask import jsonify


def success_response(data=None, status=200):
    body = {"success": True}
    if data is not None:
        body["data"] = data
    return jsonify(body), status


def error_response(
    message,
    code=None,
    fields=None,
    status=400,
):
    err = {"message": message}
    if code:
        err["code"] = code
    if fields:
        err["fields"] = fields
    return jsonify({"success": False, "error": err}), status
