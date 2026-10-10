<script setup>
import {onMounted,onUnmounted,reactive,ref,watch} from 'vue'
import {useRoute,useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {CopyDocument} from '@element-plus/icons-vue'
import {api} from '../api'
import {useUiStore} from '../stores/ui'
watch(()=>useUiStore().refreshKey,load)
import {typeName,statusName,formatTime,errorMessage} from '../utils/labels'
const router=useRouter(),route=useRoute(),filters=reactive({event_type:'',status:'',source_group:'',track_id:'',dates:[]}),page=ref(1),size=ref(10),rows=ref([]),total=ref(0),loading=ref(false),error=ref(''),selected=ref(null),drawer=ref(false),saving=ref(false)
const channelNames={console:'控制台',web:'网页通知',tts:'语音告警'}
const deliveryNames={delivered:'已投递',failed:'投递失败',skipped:'已跳过'}
const deliveryReasons={TTS_QUEUED:'已进入语音队列，等待播报',TTS_QUEUE_FULL:'语音队列已满，本条未入队',TTS_WORKER_CLOSED:'语音工作线程不可用',TTS_DUPLICATE_QUEUED:'该事件已在语音队列中',TTS_UNAVAILABLE:'语音引擎不可用，请检查服务端语音运行环境',TTS_BACKEND_FAILED:'语音引擎执行失败',TTS_FAILED:'语音服务失败',TTS_DISABLED:'语音告警已禁用',TTS_COOLDOWN:'处于语音告警冷却期',ALERT_DUPLICATE:'重复事件已跳过投递',ALERT_ADAPTER_FAILED:'告警通道执行失败'}
let receiptTimer,receiptLoading=false
watch(()=>drawer.value&&selected.value?.alert_deliveries?.items?.some(item=>item.error_code==='TTS_QUEUED'),waiting=>{
  clearInterval(receiptTimer)
  if(waiting)receiptTimer=setInterval(async()=>{
    if(receiptLoading)return
    const id=selected.value?.id
    receiptLoading=true
    try{const data=await api.event(id);if(drawer.value&&selected.value?.id===id)selected.value=data}catch{/* Keep the last verified receipt on transient failure. */}finally{receiptLoading=false}
  },1500)
})
onUnmounted(()=>clearInterval(receiptTimer))
async function load(){loading.value=true;error.value='';try{const p={limit:size.value,offset:(page.value-1)*size.value};for(const key of ['event_type','status','source_group','track_id'])if(filters[key])p[key]=filters[key];if(filters.dates?.length){p.start_at=filters.dates[0];p.end_at=filters.dates[1]}const d=await api.events(p);rows.value=d.items;total.value=d.total_count;}catch(e){error.value=errorMessage(e)}finally{loading.value=false}}
async function open(row){try{selected.value=await api.event(row.id);drawer.value=true}catch(e){ElMessage.error(errorMessage(e))}}
async function handle(handled){saving.value=true;try{selected.value=await api.handling(selected.value.id,handled);ElMessage.success('处理状态已保存');useUiStore().refresh()}catch(e){ElMessage.error(errorMessage(e))}finally{saving.value=false}}
function reset(){Object.assign(filters,{event_type:'',status:'',source_group:'',track_id:'',dates:[]});page.value=1;load()}
async function copyId(id){try{await navigator.clipboard.writeText(id);ElMessage.success('事件编号已复制')}catch{ElMessage.error('复制失败，请手动选择编号')}}
onMounted(load);watch([page,size],load)
watch(()=>route.query.id,id=>{if(typeof id==='string')open({id})},{immediate:true})
</script>
<template><div class="page-head"><div><h1>违规事件中心</h1><p>检索、查看并处理已持久化的 PPE 事件</p></div></div>
<div class="card filters"><el-select v-model="filters.event_type" placeholder="事件类型" clearable style="width:150px"><el-option v-for="(name,key) in typeName" :key="key" :label="name" :value="key"/></el-select><el-select v-model="filters.status" placeholder="处理状态" clearable style="width:145px"><el-option v-for="(name,key) in statusName" :key="key" :label="name" :value="key"/></el-select><el-select v-model="filters.source_group" placeholder="输入来源" clearable style="width:145px"><el-option label="MP4" value="mp4"/><el-option label="RTSP" value="rtsp"/><el-option v-for="i in 4" :key="i" :label="`USB ${i-1}`" :value="`usb${i-1}`"/></el-select><el-input v-model="filters.track_id" placeholder="Track ID" style="width:125px"/><el-date-picker v-model="filters.dates" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" style="width:250px"/><el-button type="primary" @click="page=1;load()">查询</el-button><el-button @click="reset">重置</el-button></div>
<div class="card section-gap"><el-alert v-if="error" type="error" :title="error" :closable="false"/><div class="table-region"><el-table height="100%" v-loading="loading" :data="rows" style="width:100%" empty-text="暂无符合条件的事件"><el-table-column label="事件编号" min-width="220"><template #default="{row}"><div class="id-cell"><el-tooltip :content="row.id"><span class="event-id">{{row.id}}</span></el-tooltip><el-button text circle aria-label="复制事件编号" @click.stop="copyId(row.id)"><el-icon><CopyDocument/></el-icon></el-button></div></template></el-table-column><el-table-column label="发生时间" min-width="180"><template #default="{row}">{{formatTime(row.timestamp)}}</template></el-table-column><el-table-column label="事件类型" min-width="135"><template #default="{row}"><el-tag :type="row.type==='PPE_UNKNOWN'?'info':'danger'">{{typeName[row.type]||row.type}}</el-tag></template></el-table-column><el-table-column prop="track_id" label="Track ID" width="100"/><el-table-column label="置信度" width="95"><template #default="{row}">{{(row.confidence*100).toFixed(1)}}%</template></el-table-column><el-table-column prop="source" label="来源" min-width="120"/><el-table-column label="证据" width="85"><template #default="{row}">{{row.snapshot?'有引用':'无'}}</template></el-table-column><el-table-column label="状态" width="105"><template #default="{row}"><el-tag :type="row.status==='resolved'?'success':'warning'">{{statusName[row.status]||row.status}}</el-tag></template></el-table-column><el-table-column label="操作" width="90"><template #default="{row}"><el-button link type="primary" @click="open(row)">查看</el-button></template></el-table-column></el-table></div><div class="pagination"><el-pagination v-model:current-page="page" v-model:page-size="size" :total="total" :pager-count="5" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next"/></div></div>
<el-drawer v-model="drawer" title="事件详情" size="min(480px,100%)"><div v-if="selected" class="stack"><div class="card"><p>事件 ID：{{selected.id}}</p><p>发生时间：{{formatTime(selected.timestamp)}}</p><p>事件类型：{{typeName[selected.type]||selected.type}}</p><p>Track ID：{{selected.track_id}}</p><p>置信度：{{(selected.confidence*100).toFixed(1)}}%</p><p>处理状态：{{statusName[selected.status]||selected.status}}</p><p>来源：{{selected.source||'未知'}}</p></div><div class="card"><h2>告警通道投递情况</h2><p class="muted">仅展示当前监控会话保留的近期事件回执；投递成功不代表人员已确认或已听到告警。</p><div v-if="selected.alert_deliveries?.items?.length" class="delivery-list" aria-label="告警通道回执"><article v-for="(receipt,index) in selected.alert_deliveries.items" :key="`${receipt.adapter}-${index}`" class="delivery-receipt"><div class="delivery-heading"><strong>{{channelNames[receipt.adapter]||receipt.adapter}}</strong><el-tag :type="receipt.status==='delivered'?'success':receipt.status==='failed'?'danger':'info'">{{receipt.error_code==='TTS_QUEUED'?'等待播报':deliveryNames[receipt.status]||receipt.status}}</el-tag></div><time class="muted">{{formatTime(receipt.timestamp)}}</time><p v-if="receipt.error_code" class="delivery-reason">{{deliveryReasons[receipt.error_code]||'通道返回原因代码，请检查服务端配置'}}<code>{{receipt.error_code}}</code></p></article></div><el-empty v-else :description="!selected.alert_deliveries?'当前后端尚未提供投递回执，请更新并重启后端':selected.alert_deliveries.recorded?'该事件无通道投递回执':'未保留投递记录，无法判断历史告警是否成功'"/></div><div class="card"><h2>证据预览</h2><img v-if="selected.snapshot" :src="api.image(selected.id)" class="evidence-image" alt="事件证据"/><el-empty v-else description="无证据引用"/><el-button type="primary" plain @click="router.push({path:'/evidence',query:{id:selected.id}})">查看完整证据</el-button></div><el-button type="primary" :loading="saving" @click="handle(selected.status!=='resolved')">{{selected.status==='resolved'?'恢复待处理':'标记已处理'}}</el-button></div></el-drawer>
</template>

<style scoped>
.delivery-list {display:grid;gap:12px;min-width:0}
.delivery-receipt {padding:12px;border:1px solid var(--border-color);border-radius:8px;min-width:0;overflow-wrap:anywhere}
.delivery-heading {display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:8px}
.delivery-reason {margin:8px 0 0;line-height:1.6}
.delivery-reason code {display:block;font-size:12px;color:var(--text-secondary);overflow-wrap:anywhere}
</style>
