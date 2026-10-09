<script setup>
import {computed,nextTick,onActivated,onDeactivated,onUnmounted,reactive,ref,watch} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {api} from '../api'
import {useUiStore} from '../stores/ui'
watch(()=>useUiStore().refreshKey,poll)
import {monitorName,typeName,statusName,formatTime,errorMessage} from '../utils/labels'
import MetricCard from '../components/common/MetricCard.vue'
const router=useRouter(),form=reactive({source_type:'mp4',location:''}),status=ref({state:'idle',recent_events:[]}),busy=ref(false),error=ref(''),previewKey=ref(0),previewError=ref(false),previewEnabled=ref(false),recentList=ref(null),mirrored=ref(false)
const active=computed(()=>['starting','running','stopping'].includes(status.value.state))
const liveFps=computed(()=>Number.isFinite(status.value.preview_fps)?`${status.value.preview_fps.toFixed(1)} FPS`:'—')
const updateDelay=computed(()=>Number.isFinite(status.value.preview_age_ms)?`${status.value.preview_age_ms} ms`:'—')
function eventTime(value){
  const parsed=Date.parse(value)
  if(Number.isFinite(parsed))return parsed
  const parts=String(value||'').match(/^(\d{4})\/(\d{1,2})\/(\d{1,2}) (\d{1,2}):(\d{2}):(\d{2})$/)
  return parts?Date.UTC(Number(parts[1]),Number(parts[2])-1,Number(parts[3]),Number(parts[4]),Number(parts[5]),Number(parts[6])):0
}
const recentEvents=computed(()=>[...(status.value.recent_events||[])].sort((a,b)=>eventTime(b.timestamp)-eventTime(a.timestamp)))
watch(()=>recentEvents.value[0]?.event_id,async(current,previous)=>{
  if(current&&current!==previous){await nextTick();recentList.value?.scrollTo({top:0})}
})
const previewUrl='/api/v1/monitor/preview'
let timer
async function poll(){try{status.value=await api.monitorStatus();error.value=''}catch(e){error.value=errorMessage(e)}}
async function start(){if(busy.value)return;busy.value=true;previewError.value=false;try{status.value=await api.monitorStart({...form,location:form.source_type==='usb_camera'?Number(form.location):form.location});previewKey.value++;ElMessage.success('监控启动请求已提交')}catch(e){ElMessage.error(errorMessage(e))}finally{busy.value=false;poll()}}
async function stop(){if(busy.value)return;busy.value=true;try{status.value=await api.monitorStop();ElMessage.success('停止请求已提交')}catch(e){ElMessage.error(errorMessage(e))}finally{busy.value=false;poll()}}
onActivated(()=>{previewEnabled.value=true;poll();if(!timer)timer=setInterval(poll,1500)})
onDeactivated(()=>{previewEnabled.value=false;clearInterval(timer);timer=null})
onUnmounted(()=>clearInterval(timer))
const metrics=computed(()=>[['已处理帧数',status.value.frames_processed,'▶'],['检测目标数',status.value.detections,'◎'],['人员轨迹观测数',status.value.tracks,'◉'],['已确认事件数',status.value.events_generated,'!'],['告警通道投递次数',status.value.alerts_delivered,'➤'],['PPE 关联未知数',status.value.unknown_associations,'?']])
</script>
<template><div class="page-head"><div><h1>实时安全监控</h1><p>单路监控 · 处理后的检测画面、事件与告警</p></div><el-tag :type="active?'success':status.state==='failed'?'danger':'info'">{{monitorName[status.state]||status.state}}</el-tag></div>
<div class="card filters"><span>输入源</span><el-select v-model="form.source_type" style="width:155px" :disabled="active"><el-option label="MP4 视频" value="mp4"/><el-option label="USB 摄像头" value="usb_camera"/><el-option label="RTSP 视频流" value="rtsp"/></el-select><el-input v-model="form.location" :type="form.source_type==='rtsp'?'password':'text'" :show-password="form.source_type==='rtsp'" :placeholder="form.source_type==='mp4'?'服务端可访问的 MP4 路径':form.source_type==='usb_camera'?'摄像头编号，例如 0':'RTSP 连接地址'" style="flex:1 1 220px" :disabled="active" autocomplete="off"/><el-button type="primary" :loading="busy" :disabled="active||!status.available||!String(form.location).trim()" @click="start">开始监控</el-button><el-button :loading="busy" :disabled="!active||status.state==='stopping'" @click="stop">停止监控</el-button></div>
<el-alert v-if="error||status.reason||status.error_message" class="section-gap" type="warning" :title="error||status.reason||status.error_message" :closable="false" />
<div class="grid-2 section-gap"><div class="card"><div class="video-panel"><div class="video-overlay"><div class="preview-telemetry" title="画面更新延迟表示最新已标注帧发布至本次状态查询的间隔，不含浏览器解码时间">实时帧率 {{liveFps}} · 更新延迟 {{updateDelay}}</div><button type="button" class="mirror-toggle" :aria-pressed="mirrored" :title="mirrored?'关闭镜像预览':'开启镜像预览'" @click="mirrored=!mirrored">{{mirrored?'取消镜像':'镜像'}}</button></div><img v-if="previewEnabled&&status.has_preview&&!previewError" :key="previewKey" :src="previewUrl" :class="{mirrored}" alt="实时处理画面" @error="previewError=true"/><div v-else-if="previewError">预览连接中断<el-button link type="primary" @click="previewError=false;previewKey++">重新连接预览</el-button></div><div v-else>{{status.state==='failed'?'视频源错误':status.state==='completed'?'视频已完成':status.state==='stopped'?'监控已停止':'等待处理画面'}}</div></div></div><div class="card monitor-events-card"><div class="monitor-events-head"><h2>最新事件</h2><span v-if="recentEvents.length" class="muted">{{recentEvents.length}} 条 · 最新在上</span></div><el-empty v-if="!recentEvents.length" description="当前会话暂无新事件"/><div v-else ref="recentList" class="event-list monitor-event-list" role="region" aria-label="最新事件滚动列表" tabindex="0"><div v-for="event in recentEvents" :key="event.event_id" class="event-item"><strong>{{typeName[event.type]||event.type}}</strong><p>{{formatTime(event.timestamp)}} · Track ID：{{event.track_id}}</p><p>处理状态：{{statusName[event.status]||event.status}}</p><img v-if="event.has_evidence" :src="api.image(event.event_id)" alt="证据缩略图" style="width:96px;height:60px;object-fit:cover;border-radius:4px"/><div><el-button link type="primary" @click="router.push({path:'/events',query:{id:event.event_id}})">查看事件详情</el-button></div></div></div></div></div>
<div class="metrics-grid section-gap"><MetricCard v-for="[label,value,icon] in metrics" :key="label" :label="label" :value="value" :icon="icon" /></div><p class="muted">检测目标和轨迹均为累计观测次数，不代表独立人员。告警投递按通道计数，可能大于事件数。</p>
</template>
