from concurrent import futures

import grpc
import cassandra_handler_pb2
import cassandra_handler_pb2_grpc


class CassandraHandler(cassandra_handler_pb2_grpc.CassandraHandlerServicer):
    def AddMessage(self, request, context):
        senderID = request.senderID
        receiverID = request.receiverID
        messageContent = request.content
        print(f'UserID {senderID} sends to UserID {receiverID}')
        print(f'Content: {messageContent}')
        print(f'Adding to DB...')
        
        # Call DB to add message

        # Return success status here
        return cassandra_handler_pb2.AddMessageRespond(ok=True)


def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cassandra_handler_pb2_grpc.add_CassandraHandlerServicer_to_server(CassandraHandler(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()