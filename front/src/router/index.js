import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
const routes=[
  {path:'/',redirect:'/overview'},
  {path:'/',component:MainLayout,children:[
    {path:'overview',name:'安全总览',component:()=>import('../views/OverviewView.vue')},
    {path:'monitoring',name:'实时监控',component:()=>import('../views/MonitoringView.vue')},
    {path:'offline',name:'离线智能检测',component:()=>import('../views/OfflineDetectionView.vue')},
    {path:'events',name:'事件中心',component:()=>import('../views/EventsView.vue')},
    {path:'evidence',name:'证据中心',component:()=>import('../views/EvidenceView.vue')},
    {path:'statistics',name:'统计分析',component:()=>import('../views/StatisticsView.vue')},
    {path:'ai-report',name:'AI 安全报告',component:()=>import('../views/AIReportView.vue')},
    {path:'ai-assistant',name:'安全助手',component:()=>import('../views/AIAssistantView.vue')}
  ]}
]
export default createRouter({history:createWebHistory(),routes})
