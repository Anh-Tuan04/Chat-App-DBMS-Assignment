from flask import Blueprint, request, jsonify, session

from modules.services.container import get_services
from utils import error_response, login_required

relationships_bp = Blueprint('relationships_bp', __name__, url_prefix='/api/relationships/')
blocks_bp = Blueprint('blocks_bp', __name__, url_prefix='/api/blocks')

@relationships_bp.route('/friends', methods=['GET', 'DELETE'])
@login_required
def friends():

    # Get list of friends
    if request.method == 'GET':
        user_id = session.get('user_id')
        users, err = get_services().relationships.get_friends(user_id)
        if err:
          return error_response("Internal server error", 500)
        return jsonify(users), 200

    # Unfriend
    else:
        friend_id = request.args.get('user_id', 0, type=int)
        if not friend_id:
            return error_response('friend id invalid', 400)

        user_id = session.get('user_id')

        if friend_id == user_id:
            return error_response('Cannot unfriend yourself', 400)

        err = get_services().relationships.unfriend(user_id, friend_id)
        if err:
          match err:
              case 'Friend not found':
                  return error_response(err, 404)
              case _:
                  return error_response('Internal server error', 500)

        # Will only get here if unfriend succeeds
        return jsonify(friend_id=friend_id), 200


@relationships_bp.route('/friend-requests', methods=['POST'])
@login_required
def friend_request():
    """Create a new friend request"""
    friend_id = request.args.get('user_id', 0, type=int)
    if not friend_id:
        return error_response('friend if invalid', 400)

    user_id = session.get('user_id')

    if friend_id == user_id:
        return error_response('Cannot send a friend request to yourself', 400)

    err = get_services().relationships.make_friend_request(user_id, friend_id)
    if err:
        match err:
            case 'Friend not exist' | 'Blocked':
                return error_response(err, 404)
            case 'Already friend' | 'Friend request already exists':
                return error_response(err, 409)
            case _:
                return error_response('Internal server error', 500)

    # Will only get to this point if a friend request is registered in DB
    return jsonify(receiver_id=friend_id), 201

    # Get friend request list
    # else:
    #     user_id = session.get('user_id')
    #     # requests are pending friend requests only, declined are not included
    #     requests, err = get_services().relationships.get_friend_requests(user_id)
    #     if err:
    #       return error_response('Internal server error', 500)
    #     return jsonify(requests), 200


@relationships_bp.route('/friend-requests/accept', methods=['POST'])
@login_required
def accept_friend_request():
    request_id = request.args.get('request_id', 0, type=int)
    if not request_id:
        return error_response('request_id invalid', 400)

    user_id = session.get('user_id')

    friend_id, err = get_services().relationships.accept_friend_request(user_id, request_id)
    if err:
      match err:
          case 'No request with this id':
              return error_response(err, 404)
          case _:
              return error_response('Internal server error', 500)

    # Will only get here if the request is accepted server side
    return jsonify(friend_id=friend_id), 200


@blocks_bp.route('', methods=['POST', 'DELETE'])
@login_required
def blocks():
    target_id = request.args.get('user_id', 0, type=int)
    if not target_id:
        return error_response('user_id is required', 400)

    user_id = session.get('user_id')
    if target_id == user_id:
        return error_response('Cannot block yourself', 400)

    if request.method == 'POST':
        err = get_services().relationships.block_user(user_id, target_id)
        if err:
            match err:
                case 'User not found':
                    return error_response(err, 404)
                case 'User is already blocked':
                    return error_response(err, 409)
                case _:
                    return error_response('Internal server error', 500)

        return jsonify(blocked_id=target_id), 201

    err = get_services().relationships.unblock_user(user_id, target_id)
    if err:
        match err:
            case 'Block not found':
                return error_response(err, 404)
            case _:
                return error_response('Internal server error', 500)

    return jsonify(unblocked_id=target_id), 200