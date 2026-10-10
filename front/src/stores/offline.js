import {defineStore} from 'pinia'
import {offlineApi} from '../api/offline'
import {terminal} from '../utils/offline'
export const useOfflineStore=defineStore('offline',{
  state:()=>({tab:'image',capabilities:null,job:null,summary:null,artifacts:[],error:'',uploading:false,uploadPercent:null,active:false,generation:0,timer:null,controller:null,uploadController:null}),
  actions:{
    remember(id){sessionStorage.setItem('offline_job_id',id)},
    stop(){this.active=false;this.generation++;clearTimeout(this.timer);this.timer=null;this.controller?.abort();this.controller=null},
    async activate(){this.stop();this.active=true;const token=this.generation;this.controller=new AbortController();try{this.capabilities=await offlineApi.capabilities(this.controller.signal);if(token!==this.generation)return;const id=this.job?.job_id||sessionStorage.getItem('offline_job_id');if(id)await this.select(id)}catch(e){if(token===this.generation)this.error=e.message}},
    async select(id){this.stop();this.active=true;this.remember(id);this.job=null;this.summary=null;this.artifacts=[];this.error='';await this.poll(id,this.generation)},
    async poll(id,token){
      if(!this.active||token!==this.generation)return
      this.controller=new AbortController()
      try{const job=await offlineApi.job(id,this.controller.signal);if(token!==this.generation)return;const first=!this.job;this.job=job;if(first)this.tab=job.media_type;this.error='';
        if(job.status==='COMPLETED'){const [summary,artifacts]=await Promise.all([offlineApi.summary(id,this.controller.signal),offlineApi.artifacts(id,this.controller.signal)]);if(token!==this.generation)return;this.summary=summary;this.artifacts=artifacts.items}
      }catch(e){if(token!==this.generation)return;this.error=e.message}
      if(this.active&&token===this.generation&&(!this.job||!terminal.has(this.job.status)))this.timer=setTimeout(()=>this.poll(id,token),1500)
    },
    async upload(file,confirmed){if(this.uploading)return;this.uploading=true;this.uploadPercent=null;this.error='';this.uploadController=new AbortController();try{const job=await offlineApi.upload(file,confirmed,e=>{this.uploadPercent=e.total?Math.min(100,Math.round(e.loaded/e.total*100)):null},this.uploadController.signal);this.remember(job.job_id);if(this.active)await this.select(job.job_id);else{this.job=job;this.summary=null;this.artifacts=[]}}catch(e){this.error=e.message;throw e}finally{this.uploading=false;this.uploadController=null}},
    async cancel(id){try{const job=await offlineApi.cancel(id);if(this.job?.job_id===id)this.job=job;return job}catch(e){this.error=e.message;throw e}}
  }
})
