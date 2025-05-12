import grpc
import calendar_pb2
import calendar_pb2_grpc

channel = grpc.insecure_channel('localhost:5471')
stub = calendar_pb2_grpc.CalendarServiceStub(channel)

# response = stub.ListEvents(calendar_pb2.ListEventsRequest(max_results=5))
# print("ListEvents called successfully.", response)

# # Create a new event
# response = stub.CreateEvent(calendar_pb2.CreateEventRequest(
#     summary='Test Event via MCP',
#     start_time='2025-05-12T10:00:00Z',
#     end_time='2025-05-12T11:00:00Z',
# ))
# print("Created Event:", response.html_link)

# List events
events_response = stub.ListEvents(calendar_pb2.ListEventsRequest(max_results=5))
for e in events_response.events:
    print(f"{e.summary}: {e.start_time} → {e.end_time}")
