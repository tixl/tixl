# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: pretix_sig1.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='pretix_sig1.proto',
  package='',
  syntax='proto3',
  serialized_options=b'\n\026eu.pretix.secrets.sig1B\014TicketProtos',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x11pretix_sig1.proto\"I\n\x06Ticket\x12\x0c\n\x04seed\x18\x01 \x01(\t\x12\x0c\n\x04item\x18\x02 \x01(\x03\x12\x11\n\tvariation\x18\x03 \x01(\x03\x12\x10\n\x08subevent\x18\x04 \x01(\x03\x42&\n\x16\x65u.pretix.secrets.sig1B\x0cTicketProtosb\x06proto3'
)




_TICKET = _descriptor.Descriptor(
  name='Ticket',
  full_name='Ticket',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='seed', full_name='Ticket.seed', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='item', full_name='Ticket.item', index=1,
      number=2, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='variation', full_name='Ticket.variation', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='subevent', full_name='Ticket.subevent', index=3,
      number=4, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=21,
  serialized_end=94,
)

DESCRIPTOR.message_types_by_name['Ticket'] = _TICKET
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Ticket = _reflection.GeneratedProtocolMessageType('Ticket', (_message.Message,), {
  'DESCRIPTOR' : _TICKET,
  '__module__' : 'pretix_sig1_pb2'
  # @@protoc_insertion_point(class_scope:Ticket)
  })
_sym_db.RegisterMessage(Ticket)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
