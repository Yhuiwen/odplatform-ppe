<script setup>
import {computed,nextTick,onMounted,onUnmounted,ref,watch} from 'vue'
import {useRoute,useRouter} from 'vue-router'
import {useUiStore} from '../stores/ui'
import {api} from '../api'
import {House,VideoCamera,Bell,Picture,DataAnalysis,Document,ChatDotRound,Fold,Expand,Refresh,Sunny,Moon} from '@element-plus/icons-vue'
const ui=useUiStore(),route=useRoute(),router=useRouter(),online=ref(false),alerts=ref(0)
const items=[['/overview','安全总览',House],['/monitoring','实时监控',VideoCamera],['/events','事件中心',Bell],['/evidence','证据中心',Picture],['/statistics','统计分析',DataAnalysis],['/ai-report','AI 安全报告',Document],['/ai-assistant','安全助手',ChatDotRound]]
const main=ref()
const scrollPositions=new Map()
watch(()=>route.path,async(next,previous)=>{
  if(previous)scrollPositions.set(previous,main.value?.scrollTop||0)
  await nextTick()
  main.value?.scrollTo({top:scrollPositions.get(next)||0,left:0})
})
const title=computed(()=>route.name||'安全总览')
let timer
async function ping(){try{await api.health();online.value=true}catch{online.value=false}}
async function loadAlerts(){try{const d=await api.statistics();alerts.value=d.by_status?.open||0}catch{alerts.value=0}}
onMounted(()=>{ping();loadAlerts();timer=setInterval(ping,15000)})
onUnmounted(()=>clearInterval(timer))
watch(()=>ui.refreshKey,loadAlerts)
watch(()=>route.path,loadAlerts)
</script>
<template><div class="shell" :class="{collapsed:ui.collapsed}">
  <aside class="sidebar"><div class="brand"><div class="brand-icon">⛑</div><div class="brand-text"><strong>ODPlatform-PPE</strong><small>智慧工地 PPE 安全运营平台</small></div></div>
    <nav><button v-for="[path,label,icon] in items" :key="path" :title="label" :aria-current="route.path===path?'page':undefined" :class="{active:route.path===path}" @click="router.push(path)"><el-icon><component :is="icon" /></el-icon><span>{{label}}</span></button></nav>
    <div class="sidebar-bottom" title="本地演示环境"><span class="dot"></span><span class="environment-text">本地演示环境</span></div>
  </aside><div class="body"><header class="toolbar"><div class="toolbar-left"><el-button text aria-label="切换导航展开" @click="ui.collapsed=!ui.collapsed"><el-icon><component :is="ui.collapsed?Expand:Fold" /></el-icon></el-button><el-breadcrumb separator="/"><el-breadcrumb-item>工作台</el-breadcrumb-item><el-breadcrumb-item>{{title}}</el-breadcrumb-item></el-breadcrumb></div><div class="toolbar-right"><el-tag type="success">本地演示</el-tag><span class="connection"><i class="dot" :class="{offline:!online}"></i>{{online?'后端已连接':'后端未连接'}}</span><el-button text aria-label="查看告警" @click="router.push('/events')"><el-badge :value="alerts" :hidden="!alerts"><el-icon><Bell /></el-icon></el-badge></el-button><el-button text aria-label="切换主题" @click="ui.toggleTheme()"><el-icon><component :is="ui.dark?Moon:Sunny" /></el-icon></el-button><el-button text aria-label="刷新页面" @click="ui.refresh()"><el-icon><Refresh /></el-icon></el-button></div></header><main ref="main" class="main" tabindex="-1"><router-view v-slot="{Component}"><keep-alive><component :is="Component" :key="route.path" /></keep-alive></router-view></main></div>
  </div></template>
