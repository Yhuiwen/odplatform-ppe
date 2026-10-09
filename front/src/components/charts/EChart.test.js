import {createApp,nextTick} from 'vue'
import {describe,it,expect,vi} from 'vitest'
const chart=vi.hoisted(()=>({setOption:vi.fn(),resize:vi.fn(),dispose:vi.fn()}))
vi.mock('echarts',()=>({init:vi.fn(()=>chart)}))
import * as echarts from 'echarts'
import EChart from './EChart.vue'
describe('chart container lifecycle',()=>{
  it('resizes the existing instance and releases observers on unmount',async()=>{
    let notify
    const disconnect=vi.fn(),observe=vi.fn()
    vi.stubGlobal('ResizeObserver',class{constructor(callback){notify=callback}observe=observe;disconnect=disconnect})
    const root=document.createElement('div');document.body.append(root)
    const app=createApp(EChart,{option:{series:[]}});app.mount(root);await nextTick()
    notify();notify()
    expect(observe).toHaveBeenCalledOnce();expect(echarts.init).toHaveBeenCalledOnce();expect(chart.resize).toHaveBeenCalledTimes(2)
    app.unmount();expect(disconnect).toHaveBeenCalledOnce();expect(chart.dispose).toHaveBeenCalledOnce()
    root.remove();vi.unstubAllGlobals()
  })
})
