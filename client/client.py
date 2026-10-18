import grpc
import chat_service_pb2
import chat_service_pb2_grpc
from datetime import datetime


# python -m grpc_tools.protoc -Iproto --python_out=client --grpc_python_out=client --pyi_out=client proto/chat_service.proto                  
def get_messages_demo(stub, conv_id):
    # 2. TEST GET MESSAGE (SELECT)
    print("\n--- 2. ĐANG LẤY DANH SÁCH TIN NHẮN (GetMessage) ---")
    messages = []
    try:
        get_req = chat_service_pb2.GetMessageForUserRequest(
            conversation_id=conv_id,
            user_id=12345,
            limit=10,
            before_message_id=0
        )
        get_resp = stub.GetMessageForUser(get_req)

        if get_resp.err:
            print(f"Lỗi từ server: {get_resp.err}")
        else:
            print(f"Lấy thành công {len(get_resp.messages)} tin nhắn:")
            messages = get_resp.messages
            for idx, item in enumerate(get_resp.messages, 1):
                print(f"  {idx}. [ID: {item.message_id}] [Sender: {item.sender_id}] {item.content}")
            
            print(f"   Next Cursor: {get_resp.next_cursor}")

    except grpc.RpcError as e:
        print(f"Lỗi gRPC khi GetMessage: {e.code()} - {e.details()}")

    return messages


def send_message_demo(stub, conv_id, sender_id):
    # 1. TEST SEND MESSAGE (INSERT)
    print("--- 1. ĐANG GỬI TIN NHẮN (SendMessage) ---")
    try:
        send_resp = stub.SendMessage(chat_service_pb2.SendMessageRequest(
            conversation_id=conv_id,
            sender_id=sender_id,
            content="Hello from " + str(datetime.now().strftime("%H:%M:%S"))
        ))
        
        if send_resp.success:
            print(f"Gửi thành công!")
        else:
            print(f"Gửi thất bại: {send_resp.err}")

    except grpc.RpcError as e:
        print(f"Lỗi gRPC khi SendMessage: {e.code()} - {e.details()}")


def delete_message_for_user_demo(stub, conv_id, msg_id, user_id):
    try:
        del_resp = stub.DeleteMessageForUser(chat_service_pb2.DeleteMessageRequest(
            conversation_id=conv_id,
            message_id=msg_id,
            user_id=user_id
        ))
            
        if del_resp.success:
            print(f"Xóa thành công")
        else:
            print(f"Xóa thất bại: {del_resp.err}")
    
    except grpc.RpcError as e:
            print(f"Lỗi gRPC khi DeleteMessage: {e.code()} - {e.details()}")


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = chat_service_pb2_grpc.MessageServiceStub(channel)

        #send_message_demo(stub, 999888777, 12345)
        messages = get_messages_demo(stub, 999888777)
        if messages:
            delete_message_for_user_demo(stub, 999888777, messages[0].message_id, 12346)
        else:
            print("Không có tin nhắn nào để xóa")

if __name__ == '__main__':
    run()