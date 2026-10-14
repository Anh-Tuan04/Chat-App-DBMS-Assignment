import grpc
import demo_pb2
import demo_pb2_grpc


def run():
    print("Sending request...")
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = demo_pb2_grpc.ScriptRunnerStub(channel)
        response = stub.Runner(demo_pb2.RunnerRequest(
            script="Sample script",
            html="sample html"))
        print("Client received modified html:")
        print(response.modifiedHtml)


if __name__ == "__main__":
    run()