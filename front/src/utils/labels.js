export const typeName={NO_HELMET:'未戴安全帽',NO_VEST:'未穿反光衣',PPE_UNKNOWN:'PPE 状态未知'}
export const statusName={open:'待处理',acknowledged:'已确认',resolved:'已处理',dismissed:'已忽略'}
export const monitorName={idle:'待启动',starting:'启动中',running:'运行中',stopping:'停止中',stopped:'已停止',completed:'视频已完成',failed:'监控失败'}
export function formatTime(value){return value?new Date(value).toLocaleString('zh-CN',{hour12:false}):'—'}
export function errorMessage(e){return e?.message||'请求失败'}
export function distribution(data){return Object.entries(data||{}).filter(([,value])=>value>0).map(([name,value])=>({name:typeName[name]||statusName[name]||name,value}))}
