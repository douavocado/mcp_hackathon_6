# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import calendar_pb2 as calendar__pb2

GRPC_GENERATED_VERSION = '1.71.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in calendar_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class CalendarServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CreateEvent = channel.unary_unary(
                '/calendar.CalendarService/CreateEvent',
                request_serializer=calendar__pb2.CreateEventRequest.SerializeToString,
                response_deserializer=calendar__pb2.CreateEventResponse.FromString,
                _registered_method=True)
        self.ListEvents = channel.unary_unary(
                '/calendar.CalendarService/ListEvents',
                request_serializer=calendar__pb2.ListEventsRequest.SerializeToString,
                response_deserializer=calendar__pb2.ListEventsResponse.FromString,
                _registered_method=True)


class CalendarServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CreateEvent(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListEvents(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_CalendarServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CreateEvent': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateEvent,
                    request_deserializer=calendar__pb2.CreateEventRequest.FromString,
                    response_serializer=calendar__pb2.CreateEventResponse.SerializeToString,
            ),
            'ListEvents': grpc.unary_unary_rpc_method_handler(
                    servicer.ListEvents,
                    request_deserializer=calendar__pb2.ListEventsRequest.FromString,
                    response_serializer=calendar__pb2.ListEventsResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'calendar.CalendarService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('calendar.CalendarService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class CalendarService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CreateEvent(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/calendar.CalendarService/CreateEvent',
            calendar__pb2.CreateEventRequest.SerializeToString,
            calendar__pb2.CreateEventResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ListEvents(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/calendar.CalendarService/ListEvents',
            calendar__pb2.ListEventsRequest.SerializeToString,
            calendar__pb2.ListEventsResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
