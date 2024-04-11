var labels = document.getElementsByTagName('label');
var inputs = document.getElementsByTagName('input');
var selects = document.getElementsByTagName('select');
var textarea = document.getElementsByTagName('textarea');
var radioes = document.getElementsByName('response');
var parent = 0;

for (label of labels){
    label.classList.add('form-label');
    label.classList.add('color-white');
    parent = label.parentNode;
    parent.classList.add('mb-3');
}

for (input of textarea){
    input.classList.add('form-control');
    input.classList.add('color-white');
    label = input.parentNode;
    parent = label.parentNode;
    parent.classList.add('mb-3');
}


for (input of inputs){
    input.classList.add('form-control');
    parent = input.parentNode;
    parent.classList.add('mb-3');
}

for (select of selects){
    select.classList.add('form-select');
    parent = select.parentNode;
    parent.classList.add('mb-3');
}

for (radio of radioes){
    radio.classList.add('form-check-input');
    parent = radio.parentNode;
    parent.classList.remove('mb-3');
    parent.classList.add('form-check-label');

    var second_parent = parent.parentNode;
    second_parent.classList.remove('mb-3');
    second_parent.classList.add('col-12');
}

function waitForLoad(id, callback){
    var timer = setInterval(function(){
        if(document.getElementById('btn-click-calc')){
            clearInterval(timer);
            callback();
        }
    }, 100);
}

waitForLoad("subm", function(){
    document.getElementById("btn-click-calc").onclick = function()
    {
        let cut_value = document.getElementById("currency_exchange").value;
        let cut_in_ir_price = document.getElementById("cut_in_ir_price").value;
        let cut_in_ir = cut_value * cut_in_ir_price;
        document.getElementById('response-calculator').innerText = cut_value + 'K cut in IR: ' + cut_in_ir;
    }
});




function btn_dropdown(id){
    let ids = id;
    let drop_down = document.getElementById("dropdown-menu-" + ids);
    if (drop_down.style.display != 'block')
    {
        drop_down.style.display = "block";
    }
    else
    {
        drop_down.style.display = "none";
    }
}



