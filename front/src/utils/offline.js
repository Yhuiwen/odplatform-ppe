export const terminal=new Set(['COMPLETED','FAILED','CANCELLED','INTERRUPTED'])
export const cancellable=new Set(['QUEUED','PROCESSING','ENCODING'])
export const stateName={VALIDATING:'校验中',QUEUED:'排队中',PROCESSING:'处理中',ENCODING:'编码校验与发布',CANCELLING:'正在取消',COMPLETED:'已完成',FAILED:'失败',CANCELLED:'已取消',INTERRUPTED:'执行中断'}
export const eventName={NO_HELMET:'未戴安全帽',NO_VEST:'未穿反光衣',PPE_UNKNOWN:'PPE 状态未知'}
export const number=value=>value==null?'—':value
export function bytes(value){
  if(!Number.isFinite(value)||value<0)return '—'
  const units=['B','KB','MB','GB'],index=value===0?0:Math.min(3,Math.floor(Math.log(value)/Math.log(1024)))
  return `${index===0?value:(value/1024**index).toFixed(2)} ${units[index]}`
}
export const confidence=value=>Number.isFinite(value)?value.toFixed(3):'—'
export const seconds=value=>Number.isFinite(value)?`${value.toFixed(2)} 秒`:'—'
export function validateFile(file,type,caps){
  const extension=file.name.split('.').pop()?.toLowerCase()
  if(!(type==='image'?['jpg','jpeg','png']:['mp4']).includes(extension))return type==='image'?'请选择 JPG/JPEG/PNG 图片':'请选择 MP4 视频'
  const max=type==='image'?caps?.max_image_bytes:caps?.max_video_bytes
  if(!max)return '尚未取得服务端上传限制'
  if(!file.size)return '文件不能为空'
  if(file.size>max)return `文件超出服务端限制 ${bytes(max)}`
  return ''
}
export function eventCount(summary){return summary?.event_analysis_status==='COMPLETED'&&summary.confirmed_events!=null?summary.confirmed_events:'未执行事件分析'}
export function timelinePosition(event,duration){return Number.isFinite(event.video_timestamp_seconds)&&duration>0?Math.max(0,Math.min(100,event.video_timestamp_seconds/duration*100)):null}
