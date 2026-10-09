<script setup>defineProps({loading:Boolean,error:String,empty:Boolean,emptyText:{type:String,default:'暂无数据'}})</script>
<template><div v-if="loading" class="empty"><el-icon class="is-loading"><Loading /></el-icon> 正在加载…</div><el-alert v-else-if="error" :title="error" type="error" show-icon :closable="false" /><el-empty v-else-if="empty" :description="emptyText" /><slot v-else /></template>
<script>import {Loading} from '@element-plus/icons-vue';export default {components:{Loading}}</script>
