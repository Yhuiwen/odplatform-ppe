import {createApp,defineComponent,nextTick,ref} from 'vue'
import {createPinia} from 'pinia'
import {createMemoryHistory,createRouter} from 'vue-router'
import ElementPlus from 'element-plus'
import {describe,expect,it,vi} from 'vitest'

vi.mock('../api',()=>({api:{health:vi.fn(async()=>({status:'ok'})),statistics:vi.fn(async()=>({by_status:{open:0}}))}}))
import MainLayout from './MainLayout.vue'

describe('module navigation',()=>{
  it('retains the previous module input and component instance',async()=>{
    let mounts=0
    const First=defineComponent({setup(){mounts++;const value=ref('');return {value}},template:'<input aria-label="保留的输入" v-model="value">'})
    const Second=defineComponent({template:'<div>第二模块</div>'})
    const router=createRouter({history:createMemoryHistory(),routes:[{path:'/',component:MainLayout,children:[{path:'first',component:First},{path:'second',component:Second}]}]})
    await router.push('/first');await router.isReady()
    const originalScrollTo=HTMLElement.prototype.scrollTo
    HTMLElement.prototype.scrollTo=vi.fn()
    const root=document.createElement('div');document.body.append(root)
    const app=createApp({template:'<router-view />'});app.config.warnHandler=()=>{}
    app.use(createPinia());app.use(router);app.use(ElementPlus);app.mount(root)
    const input=root.querySelector('input[aria-label="保留的输入"]')
    input.value='保留筛选';input.dispatchEvent(new Event('input',{bubbles:true}))
    await router.push('/second');await nextTick()
    expect(root.textContent).toContain('第二模块')
    await router.push('/first');await nextTick()
    expect(root.querySelector('input[aria-label="保留的输入"]').value).toBe('保留筛选')
    expect(mounts).toBe(1)
    app.unmount();root.remove();HTMLElement.prototype.scrollTo=originalScrollTo
  })
})
