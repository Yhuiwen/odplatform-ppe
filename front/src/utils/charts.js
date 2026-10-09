export function donutOption(data) {
  return {tooltip:{trigger:'item',formatter:'{b}<br/>{c} 条（{d}%）'},legend:{bottom:0,left:'center',width:'95%',textStyle:{fontSize:12}},series:[{type:'pie',center:['50%','42%'],radius:['40%','63%'],label:{show:false},emphasis:{label:{show:false}},data}]}
}
