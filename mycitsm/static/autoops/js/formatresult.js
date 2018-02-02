var widthfull = 400;
var progressInterval = 1000;

var widthAt = 0;
var progressTimer;
function progress_clear() {
 clearTimeout(progressTimer);
}
function progress_update() {
 widthAt=widthAt+4;
 if (widthAt > widthfull) progress_clear();
 else {
       document.getElementById('d2').style.width = widthAt + 'px';
       document.getElementById('percent').style.width = widthAt + 12 +'px';
       document.getElementById('percent').innerHTML = widthAt/4+'%';
       }
 progressTimer = setTimeout('progress_update()',progressInterval);
}



var docEle = function() {

   return document.getElementById(arguments[0]) || false;

}

function openNewDiv(_id) {

   var  m = "mask";

   if (docEle(_id)) document.removeChild(docEle(_id));

   if (docEle(m)) document.removeChild(docEle(m));

var newDiv = document.createElement("div");

   newDiv.id = _id;

   newDiv.style.position = "absolute";

   newDiv.style.zIndex = "9999";

   newDiv.style.width = "500px";

   newDiv.style.height = "300px";

   newDiv.style.top = "200px";

   newDiv.style.left = (parseInt(document.body.scrollWidth) - 500) / 2 + "px"; // 屏幕居中

   newDiv.style.background = "#B4F0FA";

   newDiv.style.border = "1px solid #0066cc";

   newDiv.style.padding = "5px";

   newDiv.innerHTML = "正在格式化磁盘，请稍后...";

   document.body.appendChild(newDiv);
   var yyy = document.getElementById('xxx');
   yyy.style.display="inline";
   
   newDiv.appendChild(yyy);

   progress_update();

   var newMask = document.createElement("div");

   newMask.id = m;

   newMask.style.position = "absolute";

   newMask.style.zIndex = "1";

   newMask.style.width = document.body.scrollWidth + "px";

   newMask.style.height = document.body.scrollHeight + "px";

   newMask.style.top = "0px";

   newMask.style.left = "0px";

   newMask.style.background = "#000";

   newMask.style.filter = "alpha(opacity=40)";

   newMask.style.opacity = "0.40";

   document.body.appendChild(newMask);

  function remove() {

   document.body.removeChild(docEle(_id));

   document.body.removeChild(docEle(m));

}


}
