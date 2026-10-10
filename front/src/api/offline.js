import {http} from './index'
const base='/offline',enc=encodeURIComponent
export const offlineApi={
  capabilities:signal=>http.get(`${base}/capabilities`,{signal}),
  upload:(file,confirmed,onUploadProgress,signal)=>{const data=new FormData();data.append('file',file);data.append('audio_discard_confirmed',String(confirmed));return http.post(`${base}/jobs`,data,{timeout:300000,onUploadProgress,signal})},
  jobs:(params,signal)=>http.get(`${base}/jobs`,{params,signal}),
  job:(id,signal)=>http.get(`${base}/jobs/${enc(id)}`,{signal}),
  cancel:id=>http.post(`${base}/jobs/${enc(id)}/cancel`),
  artifacts:(id,signal)=>http.get(`${base}/jobs/${enc(id)}/artifacts`,{signal}),
  summary:(id,signal)=>http.get(`${base}/jobs/${enc(id)}/artifacts/summary`,{signal}),
  events:(id,params,signal)=>http.get(`${base}/jobs/${enc(id)}/events`,{params,signal}),
  evidence:(id,eid,signal)=>http.get(`${base}/jobs/${enc(id)}/evidence/${enc(eid)}`,{signal}),
  artifactUrl:(id,key)=>`/api/v1${base}/jobs/${enc(id)}/artifacts/${enc(key)}`,
  originalUrl:id=>`/api/v1${base}/jobs/${enc(id)}/input-image`,
  evidenceUrl:(id,eid,variant)=>`/api/v1${base}/jobs/${enc(id)}/evidence/${enc(eid)}/image?variant=${enc(variant)}`,
  // HEAD checks the same restricted endpoint; the browser streams the GET to disk.
  download:async(id,key)=>{const url=offlineApi.artifactUrl(id,key);await http.head(`${base}/jobs/${enc(id)}/artifacts/${enc(key)}`);const a=document.createElement('a');a.href=url;a.download='';document.body.append(a);a.click();a.remove()}
}
