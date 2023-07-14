// -----------------------------------------------------------------------------
// Page Switching
// -----------------------------------------------------------------------------
function switchPageContent (pageName) {
    var file = "html/" + pageName.toLowerCase().replace(" ", "_") + ".html";
    $.ajax({
        type: "GET",
        url: file,
        success: function (result) {
            $("main").html(result);
        },
        error: function (jqXHR) {
            $("main").html(jqXHR.responseText);
        }
    });
}

$("nav.bottom ul li a").click(function () {
    switchPageContent($(this).html());
    $("nav.bottom ul li a.active").removeClass("active");
    $(this).addClass("active");
});