import {describe,it,expect,vi} from 'vitest'
import router from './index.js'
import {api,http} from '../api/index.js'

describe('七页路由与 API 调用边界',()=>{
  it('根路径进入总览，七个正式页面均可解析',()=>{
    const paths=['overview','monitoring','events','evidence','statistics','ai-report','ai-assistant']
    expect(router.resolve('/').matched[0].redirect).toBe('/overview')
    for(const path of paths)expect(router.resolve('/'+path).name).toBeTruthy()
  })
  it('事件处理只向受限端点发送处理布尔值',async()=>{
    const spy=vi.spyOn(http,'patch').mockResolvedValue({status:'resolved'})
    await api.handling('EVT-01',true)
    expect(spy).toHaveBeenCalledWith('/events/EVT-01/handling',{handled:true})
    spy.mockRestore()
  })
  it('证据图片仅通过事件 ID 构造受限 URL',()=>{
    expect(api.image('EVT-01')).toBe('/api/v1/evidence/EVT-01/image')
    expect(api.image('../secret')).toContain('%2F')
  })
  it('AI 请求等待服务端完整处理，普通查询保留短超时',async()=>{
    const spy=vi.spyOn(http,'post').mockResolvedValue({})
    await api.report({start_at:'2026-10-07',end_at:'2026-10-09'})
    await api.ask({question:'统计最近的安全事件'})
    expect(spy.mock.calls[0][2].timeout).toBe(180000)
    expect(spy.mock.calls[1][2].timeout).toBe(180000)
    expect(http.defaults.timeout).toBe(15000)
    spy.mockRestore()
  })
})
