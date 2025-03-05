# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import books_pb2 as books__pb2


class BookServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetSuggestions = channel.unary_unary(
                '/books.BookService/GetSuggestions',
                request_serializer=books__pb2.BookRequest.SerializeToString,
                response_deserializer=books__pb2.BookList.FromString,
                )


class BookServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetSuggestions(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_BookServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetSuggestions': grpc.unary_unary_rpc_method_handler(
                    servicer.GetSuggestions,
                    request_deserializer=books__pb2.BookRequest.FromString,
                    response_serializer=books__pb2.BookList.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'books.BookService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class BookService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetSuggestions(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/books.BookService/GetSuggestions',
            books__pb2.BookRequest.SerializeToString,
            books__pb2.BookList.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
