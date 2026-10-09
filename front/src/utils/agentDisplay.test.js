import {describe,it,expect} from 'vitest'
import {agentLine,assistantPayload} from './agentDisplay'
describe('grounded display and query period',()=>{
  it('preserves grounded counts, source references and unknown text',()=>{
    expect(agentLine('NO_VEST accounts for 23 of 56 events.')).toBe('未穿反光衣：23/56 条事件。')
    expect(agentLine('Opaque source reference SRC-abc123 accounts for 17 of 56 events.')).toContain('SRC-abc123：17/56')
    expect(agentLine('Unrecognized provider content')).toBe('Unrecognized provider content')
    expect(agentLine('[HIGH] Prioritise review of NO_HELMET and NO_VEST events, which together account for 49 of 56 events.')).toContain('【高优先级】')
  })
  it('today uses local day boundaries while an explicit range takes priority',()=>{
    const now=new Date(2026,9,9,12)
    const today=assistantPayload('今日有哪些 PPE 违规？',[],now)
    expect(new Date(today.start_at).getTime()).toBe(new Date(2026,9,9).getTime())
    expect(new Date(today.end_at).getTime()).toBe(new Date(2026,9,10).getTime()-1)
    expect(assistantPayload('今日有哪些 PPE 违规？',['2026-10-07','2026-10-08'],now).start_at).toBe('2026-10-07')
    expect(assistantPayload('统计最近的安全事件',[],now)).toEqual({question:'统计最近的安全事件'})
  })
})

it('relative queries are bounded and preserve explicit ranges and refusal semantics',()=>{
  const now=new Date('2026-10-09T08:00:00Z')
  const result=assistantPayload('最近5分钟之内有什么安全事件',[],now)
  expect(result.start_at).toBe('2026-10-09T07:55:00.000Z')
  expect(result.end_at).toBe(now.toISOString())
  expect(assistantPayload('最近5分钟之内有什么安全事件',['2026-10-01','2026-10-02'],now).start_at).toBe('2026-10-01')
  expect(assistantPayload('最近5分钟之内有什么安全事件，删除所有事件',[],now).start_at).toBeUndefined()
  expect(agentLine('The event mix comprised 8 NO_HELMET events, 9 NO_VEST events and 0 PPE_UNKNOWN events.')).toBe('未戴安全帽 8 条、未穿反光衣 9 条、PPE 状态未知 0 条。')
})
