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
