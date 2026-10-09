import {createApp,nextTick} from 'vue'
import {createPinia} from 'pinia'
import {createRouter,createMemoryHistory} from 'vue-router'
import ElementPlus from 'element-plus'
import {describe,it,expect,vi} from 'vitest'
const calls=vi.hoisted(()=>({events:vi.fn(async()=>({items:[],total_count:0})),event:vi.fn(async id=>({id,type:'NO_VEST',status:'open',confidence:.8}))}))
vi.mock('../api',()=>({api:calls}))
import EventsView from './EventsView.vue'
describe('linked event details',()=>{
  it('opens an event outside the current list and responds to query changes',async()=>{
    const router=createRouter({history:createMemoryHistory(),routes:[{path:'/events',component:EventsView}]})
    await router.push('/events?id=EVT-history');await router.isReady()
    const root=document.createElement('div');document.body.append(root)
    const app=createApp({template:'<router-view />'});app.config.warnHandler=()=>{}
    app.use(createPinia());app.use(router);app.use(ElementPlus);app.mount(root);await nextTick()
    expect(calls.event).toHaveBeenCalledWith('EVT-history')
    await router.push('/events?id=EVT-another');await nextTick()
    expect(calls.event).toHaveBeenCalledWith('EVT-another')
    app.unmount();root.remove()
  })
})
