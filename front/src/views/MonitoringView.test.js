import {createApp,nextTick} from 'vue'
import {createPinia} from 'pinia'
import {createMemoryHistory,createRouter} from 'vue-router'
import ElementPlus from 'element-plus'
import {describe,expect,it,vi} from 'vitest'

const calls=vi.hoisted(()=>({monitorStatus:vi.fn(async()=>({state:'running',available:true,has_preview:true,preview_fps:18.6,preview_age_ms:35,recent_events:[
  {event_id:'EVT-old',timestamp:'2026/10/9 14:49:40',type:'NO_VEST',track_id:5,status:'open',has_evidence:false},
  {event_id:'EVT-new',timestamp:'2026/10/9 14:49:50',type:'NO_HELMET',track_id:6,status:'open',has_evidence:false},
]}))}))
vi.mock('../api',()=>({api:{...calls,image:id=>`/api/v1/evidence/${id}/image`}}))
import MonitoringView from './MonitoringView.vue'

describe('monitoring latest events',()=>{
  it('renders newest first and keeps events in the dedicated scroll region',async()=>{
    const router=createRouter({history:createMemoryHistory(),routes:[{path:'/',component:MonitoringView}]})
    await router.push('/');await router.isReady()
    const root=document.createElement('div');document.body.append(root)
    const originalScrollTo=HTMLElement.prototype.scrollTo
    HTMLElement.prototype.scrollTo=vi.fn()
    const app=createApp({template:'<router-view v-slot="{ Component }"><keep-alive><component :is="Component" /></keep-alive></router-view>'})
    app.config.warnHandler=()=>{}
    app.use(createPinia());app.use(router);app.use(ElementPlus);app.mount(root)
    await vi.waitFor(()=>expect(root.querySelectorAll('.monitor-event-list .event-item').length).toBe(2))
    const items=[...root.querySelectorAll('.monitor-event-list .event-item')]
    expect(items[0].textContent).toContain('14:49:50')
    expect(items[1].textContent).toContain('14:49:40')
    expect(root.querySelector('.monitor-event-list').getAttribute('aria-label')).toBe('最新事件滚动列表')
    expect(root.querySelector('.preview-telemetry').textContent).toContain('18.6 FPS · 更新延迟 35 ms')
    expect(root.textContent).not.toContain('AnnotatedFrameRenderer')
    const mirror=root.querySelector('.mirror-toggle')
    mirror.click();await nextTick()
    expect(mirror.getAttribute('aria-pressed')).toBe('true')
    expect(root.querySelector('.video-panel img').classList.contains('mirrored')).toBe(true)
    app.unmount();root.remove();HTMLElement.prototype.scrollTo=originalScrollTo
  })
})
