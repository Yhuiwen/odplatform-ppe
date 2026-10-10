<script setup>
import {ref,computed} from 'vue'
import {offlineApi} from '../../api/offline'
import {bytes} from '../../utils/offline'
const props=defineProps({job:Object,items:{type:Array,default:()=>[]}}),busy=ref(''),error=ref('')
const names={annotated:'标注结果',detections:'detections.json',summary:'summary.json',results:'results.zip',frames:'frames.jsonl',video_verification:'video_verification.json',events:'events.json',events_csv:'events.csv',evidence_index:'evidence_index.json'}
const items=computed(()=>props.items.filter(item=>names[item.key]))
async function download(key){if(busy.value)return;busy.value=key;error.value='';try{await offlineApi.download(props.job.job_id,key)}catch(e){error.value=e.message}finally{busy.value=''}}
</script>
<template><section class="card section-gap"><h2>产物下载</h2><div class="offline-downloads"><el-button v-for="item in items" :key="item.key" :disabled="job?.status!=='COMPLETED'||!!busy" :loading="busy===item.key" @click="download(item.key)">{{names[item.key]}} · {{bytes(item.size_bytes)}}</el-button></div><el-empty v-if="!items.length" description="尚无已验证产物" :image-size="55"/><p class="muted">浏览器直接下载，不将大文件加载到 JavaScript 内存。下载期间请查看浏览器的下载状态。</p><el-alert v-if="error" :title="error" type="error" :closable="false"/></section></template>
