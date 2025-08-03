let count = 1;
document.getElementById("radio1").checked = true;
setInterval( function()
{
    nextImage();
}, 4500)

function nextImage()
{
    count++;
    if(count>4)
        {
            count = 1;
        }
    document.getElementById("radio"+count).checked = true;
}

const navbar = document.querySelector(".navbar");
        const menuButton = document.querySelector(".menu-button");        
        menuButton.addEventListener("click", () => {
            navbar.classList.toggle("show-menu");
});   