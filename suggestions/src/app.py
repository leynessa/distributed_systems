import grpc
from concurrent import futures
import logging
import suggestions_pb2
import suggestions_pb2_grpc

class SuggestionsServicer(suggestions_pb2_grpc.SuggestionsServicer):
    def GetSuggestions(self, request, context):
        suggested_books = ["Book A", "Book B", "Book C"]  # Static suggestions
        return suggestions_pb2.SuggestionResponse(suggestions=suggested_books)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    suggestions_pb2_grpc.add_SuggestionsServicer_to_server(SuggestionsServicer(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
