<script setup>
import {onMounted,onUnmounted,ref,shallowRef,watch} from 'vue'
import * as echarts from 'echarts'
const props=defineProps({option:{type:Object,required:true}}),root=ref(),instance=shallowRef()
let themeObserver,sizeObserver
function paint(){if(instance.value)instance.value.setOption({...props.option,backgroundColor:'transparent',legend:{...props.option.legend,textStyle:{color:document.documentElement.classList.contains('dark')?'#e9f1ff':'#18243b'}},textStyle:{color:document.documentElement.classList.contains('dark')?'#e9f1ff':'#18243b'}},true)}
function resize(){instance.value?.resize()}
onMounted(()=>{instance.value=echarts.init(root.value);paint();window.addEventListener('resize',resize);sizeObserver=new ResizeObserver(resize);sizeObserver.observe(root.value);themeObserver=new MutationObserver(paint);themeObserver.observe(document.documentElement,{attributes:true,attributeFilter:['class']})})
onUnmounted(()=>{window.removeEventListener('resize',resize);sizeObserver?.disconnect();themeObserver?.disconnect();instance.value?.dispose()})
watch(()=>props.option,paint,{deep:true})
</script><template><div ref="root" class="chart" /></template>
