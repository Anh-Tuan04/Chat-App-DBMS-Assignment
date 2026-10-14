import grpc
import chat_service_pb2
import chat_service_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = chat_service_pb2_grpc.MessageServiceStub(channel)
        
        conv_id = 999888777
        sender_id = 12345

        # 1. TEST SEND MESSAGE (INSERT)
        print("--- 1. ĐANG GỬI TIN NHẮN (SendMessage) ---")
        try:
            send_resp = stub.SendMessage(chat_service_pb2.SendMessageRequest(
                conversation_id=conv_id,
                sender_id=sender_id,
                content="Hello "
            ))
            
            if send_resp.success:
                print(f"Gửi thành công!")
            else:
                print(f"Gửi thất bại: {send_resp.err}")

        except grpc.RpcError as e:
            print(f"Lỗi gRPC khi SendMessage: {e.code()} - {e.details()}")

        # 2. TEST GET MESSAGE (SELECT)
        print("\n--- 2. ĐANG LẤY DANH SÁCH TIN NHẮN (GetMessage) ---")
        try:
            get_req = chat_service_pb2.GetMessageForUserRequest(
                conversation_id=conv_id,
                user_id=12453,
                limit=4,
                before_message_id=0
            )
            get_resp = stub.GetMessageForUser(get_req)

            if get_resp.err:
                print(f"Lỗi từ server: {get_resp.err}")
            else:
                print(f"Lấy thành công {len(get_resp.messages)} tin nhắn:")
                for idx, item in enumerate(get_resp.messages, 1):
                    print(f"  {idx}. [ID: {item.message_id}] [Sender: {item.sender_id}] {item.content}")
                
                print(f"   Next Cursor: {get_resp.next_cursor}")

            get_resp2 = stub.GetMessageForUser(chat_service_pb2.GetMessageForUserRequest(
                            conversation_id=conv_id,
                            user_id=12453,
                            limit=4,
                            before_message_id=get_resp.next_cursor
                        ))
            if get_resp2.err:
                print(f"Lỗi từ server: {get_resp2.err}")
            else:
                print(f"Lấy thành công {len(get_resp2.messages)} tin nhắn:")
                for idx, item in enumerate(get_resp2.messages, 1):
                    print(f"  {idx}. [ID: {item.message_id}] [Sender: {item.sender_id}] {item.content}")
                            
                print(f"   Next Cursor: {get_resp2.next_cursor}")


        except grpc.RpcError as e:
            print(f"Lỗi gRPC khi GetMessage: {e.code()} - {e.details()}")

if __name__ == '__main__':
    run()