import {describe,it,expect} from 'vitest'
import {assistantResult} from './assistantResult'
describe('assistant grounded result presentation',()=>{
  it('preserves totals, event IDs and confidence without inventing records',()=>{
    const result=assistantResult({summary:['Retrieved 132 event detail record(s).','event_details.total_count=132','id=EVT-abc; timestamp=2026-10-10T07:15:50Z; track_id=6; type=NO_HELMET; status=open; confidence=0.675781','unrecognized text'],evidence_references:['20261010/event_EVT-abc.jpg','other reference']})
    expect(result.total).toBe(132)
    expect(result.events).toHaveLength(1)
    expect(result.events[0]).toMatchObject({id:'EVT-abc',track:'6',confidence:0.675781})
    expect(result.lines).toEqual(['unrecognized text'])
    expect(result.references[0].id).toBe('EVT-abc')
    expect(result.references[1].id).toBeNull()
  })
  it('does not treat malformed or unsupported fields as events',()=>{
    expect(assistantResult({summary:['id=EVT-x; type=administrator; confidence=1']}).events).toEqual([])
    expect(assistantResult({}).total).toBeNull()
  })
})
