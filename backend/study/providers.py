import json
from django.conf import settings

class GeminiProvider:
    key_name = 'GEMINI_API_KEY'
    def request(self, key, system, schema, payload, streaming=False):
        operation = 'streamGenerateContent?alt=sse' if streaming else 'generateContent'
        return (f'https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL}:{operation}',
            {'x-goog-api-key':key},
            {'systemInstruction':{'parts':[{'text':system}]},'contents':[{'role':'user','parts':[{'text':json.dumps(payload)}]}],
             'generationConfig':{'responseMimeType':'application/json','responseJsonSchema':schema.model_json_schema(),'maxOutputTokens':6000}})
    def parse(self, data, streaming=False):
        candidate = (data.get('candidates') or [{}])[0]
        content = ''.join(p.get('text','') for p in candidate.get('content',{}).get('parts',[]) if not p.get('thought'))
        usage = data.get('usageMetadata',{})
        return content, usage.get('promptTokenCount',0), usage.get('candidatesTokenCount',0)+usage.get('thoughtsTokenCount',0)

class OpenAIProvider:
    key_name = 'OPENAI_API_KEY'
    def request(self, key, system, schema, payload, streaming=False):
        body = {'model':settings.AI_MODEL,'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(payload)}],
                'response_format':{'type':'json_schema','json_schema':{'name':schema.__name__,'strict':True,'schema':schema.model_json_schema()}},'max_completion_tokens':3500}
        if streaming: body.update(stream=True,stream_options={'include_usage':True})
        return 'https://api.openai.com/v1/chat/completions', {'Authorization':f'Bearer {key}'}, body
    def parse(self, data, streaming=False):
        choice = (data.get('choices') or [{}])[0]
        content = choice.get('delta' if streaming else 'message',{}).get('content') or ''
        usage = data.get('usage') or {}
        return content, usage.get('prompt_tokens',0), usage.get('completion_tokens',0)

PROVIDERS = {'gemini':GeminiProvider, 'openai':OpenAIProvider}

def provider_for(name):
    if name not in PROVIDERS: raise ValueError('Unsupported AI provider configuration.')
    return PROVIDERS[name]()
