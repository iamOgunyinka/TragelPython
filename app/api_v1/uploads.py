from flask import request, jsonify
from flask_login import current_user

from . import v1_api as api, images as photo_object
from ..decorators import UserType, permission_required
from ..utils import upload as upload_image, send_response


@api.route('/upload_image', methods=['POST'])
@permission_required(UserType.Administrator)
def upload_image_route():
    result = upload_image(photo_object, request, current_user.company_id, 'photo')
    url = result.get('url')
    if url is None:
        return send_response(400, result.get('error'), 'Upload not successful')
    response = jsonify({'url': url, 'status': 200, 'message': 'Upload successful'})
    response.status_code = 200
    return response
