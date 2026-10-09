import axios from 'axios'
export const http=axios.create({baseURL:'/api/v1',timeout:15000})
http.interceptors.response.use(r=>r.data,e=>Promise.reject(new Error(e.response?.data?.detail||(e.code==='ECONNABORTED'?'请求超时，请稍后重试':e.message)||'请求失败')))
export const api={
  health:()=>http.get('/health'),capabilities:()=>http.get('/capabilities'),overview:p=>http.get('/overview',{params:p}),statistics:p=>http.get('/statistics',{params:p}),
  events:p=>http.get('/events',{params:p}),event:id=>http.get(`/events/${encodeURIComponent(id)}`),handling:(id,handled)=>http.patch(`/events/${encodeURIComponent(id)}/handling`,{handled}),
  evidence:p=>http.get('/evidence',{params:p}),evidenceItem:id=>http.get(`/evidence/${encodeURIComponent(id)}`),image:id=>`/api/v1/evidence/${encodeURIComponent(id)}/image`,
  monitorStatus:()=>http.get('/monitor/status'),monitorStart:p=>http.post('/monitor/start',p),monitorStop:()=>http.post('/monitor/stop'),
  report:p=>http.post('/reports/generate',p,{timeout:180000}),ask:p=>http.post('/assistant/ask',p,{timeout:180000})
}
