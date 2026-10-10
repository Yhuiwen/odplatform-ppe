import {describe,it,expect} from 'vitest'
import {bytes,confidence} from './offline'
describe('G display formats',()=>{
 it('keeps small nonzero manifest sizes and uses automatic units',()=>{expect(bytes(12)).toBe('12 B');expect(bytes(2048)).toBe('2.00 KB');expect(bytes(1048576)).toBe('1.00 MB');expect(bytes(1073741824)).toBe('1.00 GB');expect(bytes(0)).toBe('0 B');expect(bytes(null)).toBe('—')})
 it('formats confidence without changing the raw number',()=>{const raw=.9123456789;expect(confidence(raw)).toBe('0.912');expect(raw).toBe(.9123456789);expect(confidence(null)).toBe('—')})
})
