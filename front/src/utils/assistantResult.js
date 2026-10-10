import {agentLine} from './agentDisplay'
import {typeName,statusName} from './labels'

// Only parse the known read-only projection format. Never interpret arbitrary prose as facts.
export function assistantResult(message){
  const events=[],lines=[]
  let total=null
  for(const raw of message.summary||[]){
    const metric=raw.match(/^event_details\.total_count=(\d+)$/)
    const retrieved=raw.match(/^Retrieved (\d+) event detail record\(s\)\.$/)
    if(metric||retrieved){total=Number((metric||retrieved)[1]);continue}
    const event=raw.match(/^id=(EVT-[\w-]+); timestamp=([^;]+); track_id=(\d+); type=(NO_HELMET|NO_VEST|PPE_UNKNOWN); status=(open|resolved|acknowledged|dismissed); confidence=([\d.]+)$/)
    if(event){
      const [,id,time,track,type,status,confidence]=event
      if(!events.some(item=>item.id===id))events.push({id,time,track,type:typeName[type],status:statusName[status],confidence:Number(confidence)})
    }else lines.push(agentLine(raw))
  }
  const references=[...new Set(message.evidence_references||[])].map(reference=>({reference,id:reference.match(/event_(EVT-[\w-]+)\.(?:jpg|jpeg|png)$/i)?.[1]||null}))
  return {events,lines,total,references}
}
