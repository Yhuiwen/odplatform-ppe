<script setup>defineProps({label:String,value:[Number,String],icon:{type:String,default:'▣'},hint:String})</script>
<template><div class="card metric"><div class="metric-icon">{{icon}}</div><div><small>{{label}}</small><strong>{{value??'—'}}</strong><small v-if="hint">{{hint}}</small></div></div></template>
