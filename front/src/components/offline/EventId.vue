<script setup>
import {ref,watch} from 'vue'
const props=defineProps({value:String}),error=ref(''),copied=ref(false)
watch(()=>props.value,()=>{copied.value=false;error.value=''})
async function copy(){error.value='';copied.value=false;try{await navigator.clipboard.writeText(props.value);copied.value=true}catch{error.value='复制失败，请手动选择编号复制'}}
</script>
<template><div class="offline-event-id"><el-tooltip :content="value" placement="top"><span>{{value}}</span></el-tooltip><el-button link aria-label="复制事件 ID" @click.stop="copy">{{copied?'已复制':'复制'}}</el-button></div><small v-if="error" class="error">{{error}}</small></template>
