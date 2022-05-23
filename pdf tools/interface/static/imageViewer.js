function initViewer(images, url_for=true){

    var currentImg = 0;
    var img = new Image();
    img.id = 'activeImage';
    img.src = images[currentImg];
    goTo(currentImg);


    var nextButton = $('<input />', {
        type: 'button',
        value: '-->',
        id: 'nextBtn',
        on: {
            click: nextImage
        }
    });
    var prevButton = $('<input />', {
        type: 'button',
        value: '<--',
        id: 'prevBtn',
        on: {
            click: previousImage
        }
    });
    var pgNum = $('<input />', {
        type: 'text',
        value: currentImg + 1,
        id: 'currentPg',
        size: 2
    });
    pgNum.change(function (){
        goTo($(this).val()-1)
    })

    function goTo(n) {
        if (0 <= n && n <= images.length){
            currentImg = n;
            $('#currentPg').val(currentImg+1);
            $('#activeImage').attr("src", images[currentImg]);
        } else {
            console.log("out of bounds!");
            $('#currentPg').val(currentImg+1);
        }
    }
    function nextImage() {
        if (currentImg < images.length-1) {
            goTo(currentImg+1);
        }
        console.log(currentImg)
    }
    function previousImage() {
        if (currentImg > 0) {
            goTo(currentImg-1);
        }
        console.log(currentImg)
    }

    var topBar = $('<div />', {
        id: 'viewer-controls'
    }).appendTo("#imgviewer");

    $("#viewer-controls").append(prevButton);
    $("#viewer-controls").append(pgNum);
    $("#viewer-controls").append(nextButton);
    $("#imgviewer").append(img);
    console.log("Done!")
}


function waitForElm(selector) {
    return new Promise(resolve => {
        if (document.querySelector(selector)) {
            return resolve(document.querySelector(selector));
        }

        const observer = new MutationObserver(mutations => {
            if (document.querySelector(selector)) {
                resolve(document.querySelector(selector));
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}