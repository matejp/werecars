//****************************************
// JQuert plugin za branje url parametrov
//****************************************
// example.com?param1=name&param2=&id=6
// $.urlParam('param1'); // name
// $.urlParam('id');        // 6
// $.urlParam('param2');  
$.urlParam = function(name){
    var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
    return results[1] || 0;
}