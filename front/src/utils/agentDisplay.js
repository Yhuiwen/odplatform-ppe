import {typeName} from './labels'
// Display-only translations of recognized grounded sentences. Unknown text is retained.
const rules=[
  [/^Retrieved (\d+) event detail record\(s\)\.$/,n=>`在所选范围内查询到 ${n} 条已保存事件。`],
  [/^event_details\.total_count=(\d+)$/,n=>`查询范围内共 ${n} 条事件。`],
  [/^(\d+) events remained open and (\d+) were resolved; no events were acknowledged or dismissed\.$/,(a,b)=>`${a} 条事件待处理，${b} 条已处理；没有已确认或已忽略事件。`],
  [/^(\d+) persisted events were recorded in the reporting period from (.+) to (.+)\.$/,(n,a,b)=>`报告范围 ${a} 至 ${b} 内记录了 ${n} 条持久化事件。`],
  [/^The event mix comprised (\d+) NO_HELMET events, (\d+) NO_VEST events and (\d+) PPE_UNKNOWN events\.$/,(a,b,c)=>`未戴安全帽 ${a} 条、未穿反光衣 ${b} 条、PPE 状态未知 ${c} 条。`],
  [/^All (\d+) events fall on UTC day (\d{4}-\d\d-\d\d)\.$/,(n,d)=>`全部 ${n} 条事件发生于 UTC 日期 ${d}。`],
  [/^Events span from (.+) to (.+) within the reporting period\.$/,(a,b)=>`报告范围内事件时间：${a} 至 ${b}。`],
  [/^Opaque source reference (SRC-[a-z0-9]+) accounted for (\d+) events and (SRC-[a-z0-9]+) for (\d+) events\.$/,(a,n,b,m)=>`来源引用 ${a} 有 ${n} 条事件，${b} 有 ${m} 条事件。`],
  [/^All (\d+) events have a persisted relative snapshot reference and none are missing evidence\.$/,n=>`${n} 条事件均有持久化证据引用，没有缺少引用的事件。`],
  [/^(\d+) events remain open and (\d+) are resolved; no events are recorded as acknowledged or dismissed\.$/,(a,b)=>`${a} 条事件待处理，${b} 条已处理；没有已确认或已忽略事件。`],
  [/^The reporting period contains (\d+) persisted PPE-related events\.$/,n=>`报告范围内共有 ${n} 条已持久化 PPE 事件。`],
  [/^NO_HELMET accounts for (\d+) events, NO_VEST for (\d+) events and PPE_UNKNOWN for (\d+) events\.$/,(a,b,c)=>`未戴安全帽 ${a} 条、未穿反光衣 ${b} 条、PPE 状态未知 ${c} 条。`],
  [/^(\d+) events occurred on UTC day (\d{4}-\d\d-\d\d)\.$/,(n,d)=>`UTC 日期 ${d} 记录 ${n} 条事件。`],
  [/^Every persisted event has a relative snapshot reference, so evidence coverage is complete for the reporting period\.$/,()=>`报告范围内每条已持久化事件都有相对路径证据引用，引用覆盖完整。`],
  [/^Persisted events span from (.+) to (.+)\.$/,(a,b)=>`持久化事件时间范围：${a} 至 ${b}。`],
  [/^Opaque source reference (SRC-[a-z0-9]+) accounts for (\d+) of (\d+) events\.$/,(s,n,t)=>`来源引用 ${s}：${n}/${t} 条事件。`],
  [/^(\d+) of (\d+) events are still open at the end of the reporting period\.$/,(n,t)=>`报告范围内 ${n}/${t} 条事件仍待处理。`],
  [/^Tracker-scoped track_id (\d+) has (\d+) events; this is not a stable person identity count\.$/,(id,n)=>`跟踪范围内 Track ID ${id} 有 ${n} 条事件；不能视为独立人员数。`],
  [/^Tracker-scoped track_id (\d+) has the highest event count at (\d+) events; this is not a stable person identity count\.$/,(id,n)=>`跟踪范围内 Track ID ${id} 的事件最多（${n} 条）；不能视为独立人员数。`],
  [/^(NO_HELMET|NO_VEST|PPE_UNKNOWN) is the most frequent event type with (\d+) of (\d+) events\.$/,(k,n,t)=>`${typeName[k]}记录最多：${n}/${t} 条事件。`],
  [/^(NO_HELMET|NO_VEST|PPE_UNKNOWN) accounts for (\d+) of (\d+) events\.$/,(k,n,t)=>`${typeName[k]}：${n}/${t} 条事件。`],
  [/^(\d+) PPE_UNKNOWN events indicate cases where PPE state could not be classified, limiting the reliability of compliance totals\.$/,n=>`${n} 条 PPE 状态未知事件无法分类，限制了合规统计的可靠性。`],
  [/^Event volume is concentrated on UTC day (\S+) with (\d+) events versus (\d+) on (\S+), so period totals are dominated by a single day\.$/,(a,n,m,b)=>`事件集中在 UTC 日期 ${a}（${n} 条），${b} 为 ${m} 条；报告总量主要来自单日。`],
  [/^(\d+) NO_HELMET events indicate repeated head-protection non-compliance observations in the reporting period\.$/,n=>`报告范围内有 ${n} 条未戴安全帽事件，存在重复的未佩戴观测。`],
  [/^(\d+) of (\d+) events remain open, indicating a large unresolved backlog within the reporting period\.$/,(n,t)=>`${n}/${t} 条事件仍待处理，报告范围内有较多未处理记录。`],
  [/^Event volume is unevenly distributed across opaque source references, with (SRC-[a-z0-9]+) contributing (\d+) of (\d+) events\.$/,(s,n,t)=>`来源引用的事件分布不均，${s} 占 ${n}/${t} 条。`],
  [/^Tracker-scoped track_ids (.+) account for (\d+) of (\d+) events; these counts are tracker-scoped and are not stable person identity counts\.$/,(ids,n,t)=>`跟踪范围内轨迹 ${ids} 占 ${n}/${t} 条事件；不能视为独立人员数。`],
  [/^Prioritise review of NO_HELMET and NO_VEST events, which together account for (\d+) of (\d+) events\.$/,(n,t)=>`优先复核未戴安全帽及未穿反光衣事件，共 ${n}/${t} 条。`],
  [/^Review the concentration of events on UTC day (\S+), which accounts for (\d+) of (\d+) events\.$/,(d,n,t)=>`复核 UTC 日期 ${d} 的事件集中情况，占 ${n}/${t} 条。`],
  [/^Inspect the (\d+) PPE_UNKNOWN events to determine whether detection confidence or scene conditions are limiting classification\.$/,n=>`检查 ${n} 条 PPE 状态未知事件，评估检测置信度或场景条件对分类的影响。`],
  [/^Review the opaque source reference with the largest share of events to understand whether capture coverage is uneven\.$/,()=>`复核事件占比最高的来源引用，了解采集覆盖是否不均。`],
  [/^Review the tracker-scoped tracks with the highest event counts, treating track_id as tracker-scoped and not as stable person identity\.$/,()=>`复核事件最多的跟踪轨迹；Track ID 仅在跟踪范围内有效，不能作为人员身份。`],
  [/^Review the (\d+) open events and triage them against the persisted snapshot references before the next reporting period\.$/,n=>`在下一报告周期前，结合持久化证据引用复核并分流 ${n} 条待处理事件。`],
]
export function agentLine(value){
  if(value==='The request is outside the supported read-only scope.')return '该请求超出当前支持的只读查询范围。'
  const priority=value?.match(/^\[(HIGH|MEDIUM|LOW)\] (.+)$/)
  if(priority){const translated=agentLine(priority[2]);return translated===priority[2]?value:`【${{HIGH:'高',MEDIUM:'中',LOW:'低'}[priority[1]]}优先级】${translated}`}
  for(const [pattern,translate] of rules){const match=value?.match(pattern);if(match)return translate(...match.slice(1))}
  return value
}
export function agentStatus(status=''){
  if(status==='empty')return '所选时间范围暂无已持久化事件'
  if(status.startsWith('out_of_scope'))return '超出只读查询范围'
  if(status.startsWith('refused'))return '请求已被安全边界拒绝'
  if(status.includes('assistant_fallback'))return '本地查询 / 安全降级'
  if(status.includes('assistant_llm'))return 'Provider 已验证'
  if(status.includes('TEMPLATE_FALLBACK')||status.includes(' / degraded /'))return '本地模板降级'
  if(status.includes('grounding=valid'))return '依据校验通过'
  if(status.startsWith('success'))return '受控只读查询成功'
  return '服务未返回可用结果'
}
export function assistantPayload(question,dates=[],now=new Date()){
  const payload={question}
  if(dates?.length===2){payload.start_at=dates[0];payload.end_at=dates[1]}
  else if(relativeMinutes(question)!==null){
    payload.start_at=new Date(now.getTime()-relativeMinutes(question)*60000).toISOString()
    payload.end_at=now.toISOString()
  }
  else if(question.includes('今日')||question.includes('今天')){
    payload.start_at=new Date(now.getFullYear(),now.getMonth(),now.getDate()).toISOString()
    payload.end_at=new Date(now.getFullYear(),now.getMonth(),now.getDate()+1,0,0,0,-1).toISOString()
  }
  return payload
}
export function relativeMinutes(question){
  const match=question.trim().match(/^最近\s*([1-9]\d{0,3})\s*(分钟|小时|天)(?:之内|内)?\s*(?:有(?:哪些|什么)|发生了哪些|有哪些)?\s*(?:PPE\s*违规|安全事件|违规事件)[？?]?$/)
  if(!match)return null
  const minutes=Number(match[1])*{'分钟':1,'小时':60,'天':1440}[match[2]]
  return minutes<=10080?minutes:null
}
