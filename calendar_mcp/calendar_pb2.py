# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: calendar.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'calendar.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x63\x61lendar.proto\x12\x08\x63\x61lendar\"K\n\x12\x43reateEventRequest\x12\x0f\n\x07summary\x18\x01 \x01(\t\x12\x12\n\nstart_time\x18\x02 \x01(\t\x12\x10\n\x08\x65nd_time\x18\x03 \x01(\t\":\n\x13\x43reateEventResponse\x12\x10\n\x08\x65vent_id\x18\x01 \x01(\t\x12\x11\n\thtml_link\x18\x02 \x01(\t\"(\n\x11ListEventsRequest\x12\x13\n\x0bmax_results\x18\x01 \x01(\x05\">\n\x05\x45vent\x12\x0f\n\x07summary\x18\x01 \x01(\t\x12\x12\n\nstart_time\x18\x02 \x01(\t\x12\x10\n\x08\x65nd_time\x18\x03 \x01(\t\"5\n\x12ListEventsResponse\x12\x1f\n\x06\x65vents\x18\x01 \x03(\x0b\x32\x0f.calendar.Event2\xa6\x01\n\x0f\x43\x61lendarService\x12J\n\x0b\x43reateEvent\x12\x1c.calendar.CreateEventRequest\x1a\x1d.calendar.CreateEventResponse\x12G\n\nListEvents\x12\x1b.calendar.ListEventsRequest\x1a\x1c.calendar.ListEventsResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'calendar_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CREATEEVENTREQUEST']._serialized_start=28
  _globals['_CREATEEVENTREQUEST']._serialized_end=103
  _globals['_CREATEEVENTRESPONSE']._serialized_start=105
  _globals['_CREATEEVENTRESPONSE']._serialized_end=163
  _globals['_LISTEVENTSREQUEST']._serialized_start=165
  _globals['_LISTEVENTSREQUEST']._serialized_end=205
  _globals['_EVENT']._serialized_start=207
  _globals['_EVENT']._serialized_end=269
  _globals['_LISTEVENTSRESPONSE']._serialized_start=271
  _globals['_LISTEVENTSRESPONSE']._serialized_end=324
  _globals['_CALENDARSERVICE']._serialized_start=327
  _globals['_CALENDARSERVICE']._serialized_end=493
# @@protoc_insertion_point(module_scope)
