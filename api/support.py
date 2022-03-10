from rest_framework.views import exception_handler


def beautify_errors(error_dict):
    if not error_dict:
        return error_dict
    for key in error_dict:
        error_dict[key] = error_dict[key][0]
    return error_dict


def make_real_none(value):
    value = None if str(value) == "None" else value
    return value


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data['success']['data'] = make_real_none(response.data['success']['data'])
        response.data['success']['message'] = make_real_none(response.data['success']['message'])
        response.data['errors'] = make_real_none(response.data['errors'])
        response.data['warnings'] = make_real_none(response.data['warnings'])
    return response