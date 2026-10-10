<script setup>
import {computed,onActivated,onDeactivated,onUnmounted,watch} from 'vue'
import {useOfflineStore} from '../stores/offline'
import {useUiStore} from '../stores/ui'
import OfflineUploader from '../components/offline/OfflineUploader.vue'
import OfflineTaskProgress from '../components/offline/OfflineTaskProgress.vue'
import OfflineArtifactDownloads from '../components/offline/OfflineArtifactDownloads.vue'
import ImageDetectionPanel from '../components/offline/ImageDetectionPanel.vue'
import VideoDetectionPanel from '../components/offline/VideoDetectionPanel.vue'
import OfflineTaskHistory from '../components/offline/OfflineTaskHistory.vue'
const store=useOfflineStore(),current=computed(()=>store.job?.media_type===store.tab)
onActivated(()=>store.activate());onDeactivated(()=>store.stop());onUnmounted(()=>{store.stop();store.uploadController?.abort()})
watch(()=>useUiStore().refreshKey,()=>{if(store.active)store.activate()})
</script>
<template><div class="offline-page"><div class="page-head"><div><h1>离线智能检测</h1><p>上传图片或视频，进行 PPE 检测、违规分析与证据导出。</p></div><div class="filters"><el-tag :type="store.capabilities?.image_processor_available?'success':'warning'">图片{{store.capabilities?.image_processor_available?'可用':'不可用'}}</el-tag><el-tag :type="store.capabilities?.video_processor_available?'success':'warning'">视频{{store.capabilities?.video_processor_available?'可用':'不可用'}}</el-tag><el-tag :type="store.capabilities?.event_analysis_available?'success':'info'">事件分析{{store.capabilities?.event_analysis_available?'可用':'不可用'}}</el-tag><el-button @click="store.tab='history'">历史任务</el-button></div></div>
<el-alert v-if="store.error" class="offline-error" :title="store.error" type="error" :closable="false"/>
<el-tabs v-model="store.tab"><el-tab-pane label="图片检测" name="image"/><el-tab-pane label="视频检测" name="video"/><el-tab-pane label="任务历史" name="history"/></el-tabs>
<OfflineTaskHistory v-if="store.tab==='history'" @select="store.select"/>
<template v-else><OfflineUploader :key="store.tab" :type="store.tab"/><OfflineTaskProgress v-if="current"/><template v-if="current&&store.job?.status==='COMPLETED'&&store.summary"><ImageDetectionPanel v-if="store.tab==='image'" :job="store.job" :summary="store.summary"/><VideoDetectionPanel v-else :job="store.job" :summary="store.summary"/><OfflineArtifactDownloads :job="store.job" :items="store.artifacts"/></template><el-empty v-else-if="!current" description="选择文件开始检测，或从历史任务恢复结果" :image-size="65"/></template>
</div></template>
