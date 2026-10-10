<script setup>
import {computed,ref} from 'vue'
import {ElMessage,ElMessageBox} from 'element-plus'
import {UploadFilled} from '@element-plus/icons-vue'
import {useOfflineStore} from '../../stores/offline'
import {bytes,validateFile} from '../../utils/offline'
const props=defineProps({type:String})
const store=useOfflineStore(),file=ref(null),error=ref('')
const available=computed(()=>props.type==='image'?store.capabilities?.image_processor_available:store.capabilities?.video_processor_available)
const limit=computed(()=>props.type==='image'?store.capabilities?.max_image_bytes:store.capabilities?.max_video_bytes)
function change(item){error.value=validateFile(item.raw,props.type,store.capabilities);file.value=error.value?null:item.raw}
async function start(){
  if(!file.value||store.uploading||!available.value)return
  let confirmed=false
  // Browser metadata cannot reliably expose audio tracks; require explicit consent
  // before any MP4 upload. Server remains authoritative for actual audio presence.
  if(props.type==='video'){try{await ElMessageBox.confirm('当前版本导出的标注视频不保留原始音轨，是否继续？浏览器无法可靠确认音轨，服务端将校验实际视频。','音轨确认',{confirmButtonText:'同意移除音轨并继续',cancelButtonText:'取消',type:'warning'});confirmed=true}catch{return}}
  try{await store.upload(file.value,confirmed)}catch(e){ElMessage.error(e.message)}
}
</script>
<template><section class="card offline-upload"><div><h2>{{type==='image'?'上传图片':'上传视频'}}</h2><p class="muted">{{type==='image'?'JPG / JPEG / PNG · 保留原始文件':'MP4 · 原分辨率逐帧处理'}} · 上限 {{limit?bytes(limit):'读取中'}}</p></div>
<el-upload drag :auto-upload="false" :show-file-list="false" :disabled="store.uploading||!available" :accept="type==='image'?'.jpg,.jpeg,.png':'.mp4'" :on-change="change"><el-icon class="el-icon--upload"><UploadFilled/></el-icon><div>拖拽文件到此处，或点击选择</div></el-upload>
<div class="offline-upload-info"><span v-if="file">{{file.name}} · {{bytes(file.size)}}</span><span v-else class="muted">尚未选择文件</span><el-button type="primary" :disabled="!file||!available||store.uploading" :loading="store.uploading" @click="start">{{store.uploading?'上传与服务端校验中':'开始检测'}}</el-button></div>
<el-progress v-if="store.uploading" :percentage="store.uploadPercent??0" :indeterminate="store.uploadPercent==null"/><p v-if="store.uploading" class="muted">上传进度：{{store.uploadPercent==null?'总字节数未知':`${store.uploadPercent}%`}}；上传完成后仍需后台处理。</p>
<el-alert v-if="error" :title="error" type="error" :closable="false"/><el-alert v-if="store.capabilities&&!available" :title="(type==='image'?store.capabilities.image_processor_reason:store.capabilities.video_processor_reason)||'当前未授权执行，请查看后端配置'" type="warning" :closable="false"/>
</section></template>
