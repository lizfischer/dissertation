function initViewer(images){

    var currentImg = 0;
    var img = $('<img />', {
        id: 'activeImage',
        src: images[currentImg]
    });

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

    function goTo(n) {
        if (0 <= n <= images.length){
            currentImg += n
            $('#activeImage').attr("src", images[currentImg]);
        }
    }
    function nextImage() {
        if (currentImg < images.length-1) {
            currentImg += 1
            $('#activeImage').attr("src", images[currentImg]);
        }
        console.log(currentImg)
    }
    function previousImage() {
        if (currentImg > 0) {
            currentImg -= 1
            $('#activeImage').attr("src", images[currentImg]);
        }
        console.log(currentImg)
    }

    $("#imgviewer").append(prevButton);
    $("#imgviewer").append(nextButton);
    $("#imgviewer").append(img);
    return $("#imgviewer");
}
