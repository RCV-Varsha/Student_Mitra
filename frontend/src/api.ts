let csrf = '';
export async function api(path:string, method='GET', data?:unknown):Promise<any> {
  const form = data instanceof FormData;
  const response = await fetch('/api'+path,{method,credentials:'same-origin',headers:{...(form?{}:{'Content-Type':'application/json'}),...(method==='GET'?{}:{'X-CSRFToken':csrf})},body:data===undefined?undefined:form?data:JSON.stringify(data)});
  const result = response.status===204?{}:await response.json().catch(()=>({detail:'Server unavailable. Please retry.'}));
  if (!response.ok) throw new Error(typeof result.detail==='string'?result.detail:JSON.stringify(result));
  if(result.csrf) csrf=result.csrf;
  return result;
}
export const key = () => crypto.randomUUID();
export async function streamTutor(path:string,data:unknown,onDraft:(text:string)=>void):Promise<any>{
  const response=await fetch('/api'+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrf},body:JSON.stringify(data)});
  if(!response.ok){const error=await response.json();throw new Error(error.detail||'Tutor unavailable. Please retry.')}
  if(!response.body)throw new Error('Streaming is unavailable in this browser.');
  const reader=response.body.getReader(), decoder=new TextDecoder();let buffer='',result:any=null;
  try{while(true){const {done,value}=await reader.read();buffer+=decoder.decode(value,{stream:!done});let end;
    while((end=buffer.indexOf('\n\n'))>=0){const block=buffer.slice(0,end);buffer=buffer.slice(end+2);const event=block.split('\n').find(x=>x.startsWith('event:'))?.slice(6).trim();const raw=block.split('\n').find(x=>x.startsWith('data:'))?.slice(5);if(!raw)continue;const item=JSON.parse(raw);if(event==='draft')onDraft(item.answer);if(event==='error')throw new Error(item.detail);if(event==='complete')result=item;}
    if(done)break;
  }}finally{reader.releaseLock()}
  if(!result)throw new Error('Connection interrupted. Retry to recover a completed answer.');
  return result;
}
