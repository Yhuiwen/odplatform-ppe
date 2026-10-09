import { defineStore } from 'pinia'
export const useUiStore=defineStore('ui',{state:()=>({collapsed:false,dark:false,refreshKey:0}),actions:{toggleTheme(){this.dark=!this.dark;document.documentElement.classList.toggle('dark',this.dark)},refresh(){this.refreshKey++}}})
