"""SSE transport; drafts are untrusted until the final validated message arrives."""
import json
from queue import Queue, Empty
from threading import Thread, BoundedSemaphore
from django.db import close_old_connections
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .ai import stream_callback, AIError
from .learning import owned, tutor
from .serializers import TutorInput, MessageSerializer
slots = BoundedSemaphore(4)

@api_view(['POST'])
def tutor_stream(request, pk):
    project = owned(request.user,pk)
    data = TutorInput(data=request.data)
    data.is_valid(raise_exception=True)
    if not slots.acquire(blocking=False): return Response({'detail':'Tutor is busy. Please retry shortly.'},status=429)
    queue = Queue()
    def work():
        close_old_connections()
        token = stream_callback.set(lambda text:queue.put(('draft',{'answer':text})))
        try:
            message = tutor(request.user,project,**data.validated_data)
            queue.put(('complete',dict(MessageSerializer(message).data)))
        except (AIError,ValueError) as e: queue.put(('error',{'detail':str(e)}))
        except Exception: queue.put(('error',{'detail':'Tutor interrupted. Retry the same question; completed answers are preserved.'}))
        finally:
            stream_callback.reset(token)
            close_old_connections()
            queue.put(None)
            slots.release()
    Thread(target=work,daemon=True).start()
    def events():
        yield 'event: status\ndata: {"detail":"Retrieving project evidence…"}\n\n'
        while True:
            try: item = queue.get(timeout=10)
            except Empty:
                yield ': heartbeat\n\n'
                continue
            if item is None: break
            name,body = item
            yield f'event: {name}\ndata: {json.dumps(body)}\n\n'
    response = StreamingHttpResponse(events(),content_type='text/event-stream')
    response['Cache-Control']='no-cache, no-store'
    response['X-Accel-Buffering']='no'
    return response
