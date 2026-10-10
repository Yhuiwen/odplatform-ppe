<script setup>
import {computed} from 'vue'
import {ElMessage} from 'element-plus'
import {useOfflineStore} from '../../stores/offline'
import {cancellable,number,stateName} from '../../utils/offline'
const store=useOfflineStore(),job=computed(()=>store.job)
async function cancel(){try{await store.cancel(job.value.job_id)}catch(e){ElMessage.error(e.message)}}
</script>
<template><section v-if="job" class="card section-gap"><div class="offline-upload-info"><div><strong>{{job.original_filename}}</strong><p class="muted">任务 {{job.job_id}}</p></div><div class="filters"><el-tag :type="job.status==='FAILED'?'danger':job.status==='COMPLETED'?'success':'info'">{{stateName[job.status]||job.status}}</el-tag><el-button v-if="cancellable.has(job.status)" @click="cancel">取消任务</el-button></div></div>
<el-progress :percentage="job.progress_percent??0" :indeterminate="job.progress_percent==null" :status="job.status==='COMPLETED'?'success':job.status==='FAILED'?'exception':undefined"/>
<p class="muted">后台处理：{{number(job.processed_frames)}} / {{number(job.total_frames)}} 帧 · {{job.progress_percent==null?'总进度未知':`${job.progress_percent}%`}}。编码验证与发布完成后才可查看结果。</p>
<p v-if="job.media_type==='video'" class="muted">服务端已验收输入：{{number(job.input_width)}} × {{number(job.input_height)}} · {{number(job.input_fps)}} FPS · {{number(job.input_duration_seconds)}} 秒 · {{job.has_audio?'含音轨（已明确同意移除）':'无音轨'}}。逐帧 CFR 与输出完整性仍由 Worker 校验。</p>
<el-alert v-if="job.error_message" :title="`${job.error_code}：${job.error_message}`" type="error" :closable="false"/>
</section></template>
