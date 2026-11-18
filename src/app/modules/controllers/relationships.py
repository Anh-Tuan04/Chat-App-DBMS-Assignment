from flask import Blueprint, request, jsonify, session

from ...utils import error_response, login_required

relationships_bp = Blueprint('relationships_bp', __name__, url_prefix='/api/relationships/')


@relationships_bp.route('/friends', methods=['GET', 'DELETE'])
@login_required
def friends():

    # Get list of friends
    if request.method == 'GET':
        user_id = session.get('user_id')

        # TODO: call service
        # users, err = get_friends_service(user_id)
        # if err:
        #   return error_response("Internal server error", 500)
        
        # hardcoded response
        users = [
            {
                "friend_id": 7,
                "friend_username": "jane_doe",
                "friend_display_name": "Jane Doe",
                "friend_avatar_url": "",
                "friend_online_status": "online"
            },
            {
                "friend_id": 21,
                "friend_username": "mike99",
                "friend_display_name": "Mike",
                "friend_avatar_url": "",
                "friend_online_status": "offline"
            }
        ]

        return jsonify(users), 200

    # Unfriend
    else:
        friend_id = request.args.get('user_id', 0, type=int)
        if not friend_id:
            return error_response('friend id invalid', 400)

        user_id = session.get('user_id')

        if friend_id == user_id:
            return error_response('Cannot unfriend yourself', 400)
        # TODO: call service
        # err = unfriend_service(user_id, friend_id)
        # if err:
        #   match err:
        #       case 'Friend not found':
        #           return error_response(err, 404)
        #       case _:
        #           return error_response('Internal server error', 500)

        # Will only get here if unfriend succeeds
        return jsonify(friend_id=friend_id), 200


@relationships_bp.route('/friend-request', methods=['GET', 'POST'])
@login_required
def friend_request():

    # Make friend request
    if request.method == 'POST':
        friend_id = request.args.get('user_id', 0, type=int)
        if not friend_id:
            return error_response('friend if invalid', 400)

        user_id = session.get('user_id')

        if friend_id == user_id:
            return error_response('Cannot send a friend request to yourself', 400)
        # TODO: call service
        # err = make_friend_request_service(user_id, friend_id)
        # if err:
        #   match err:
        #       case 'Friend not exist' | 'Blocked':
        #           return error_response(err, 404)
        #       case 'Already friend':
        #           return error_response(err, 409)
        #       case _:
        #           return error_response('Internal server error', 500)

        # Will only get to this point if a friend request is registered in DB
        return jsonify(receiver_id=friend_id), 200

    # Get friend request list
    else:
        user_id = session.get('user_id')

        # TODO: call service
        # requests are pending friend requests only, declined are not included
        # requests, err = get_friend_request_service(user_id)
        # if err:
        #   return error_response('Internal server error', 500)
        
        # hardcoded response
        requests = [
            {
                "request_id": 15,
                "requester_id": 7,
                "requester_username": "jane_doe",
                "requester_display_name": "Jane Doe",
                "requester_avatar_url": "",
                "created_at": "2026-10-29T09:20:00Z"
            },
            {
                "request_id": 12,
                "requester_id": 21,
                "requester_username": "mike99",
                "requester_display_name": "Mike",
                "requester_avatar_url": "",
                "created_at": "2026-10-28T14:05:00Z"
            }
        ]

        return jsonify(requests), 200


@relationships_bp.route('/friend-requests/accept', methods=['POST'])
@login_required
def accept_friend_request():
    request_id = request.args.get('request_id', 0, type=int)
    if not request_id:
        return error_response('request_id invalid', 400)

    user_id = session.get('user_id')

    # TODO: call service
    # err = accept_friend_request_service(user_id, request_id)
    # if err:
    #   match err:
    #       case 'No request with this id':
    #           return error_response(err, 404)
    #       case _:
    #           return error_response('Internal server error', 500)

    # Will only get here if the request is accepted server side
    return jsonify(friend_id=request_id), 200