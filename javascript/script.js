// -----------------------------------------------------------------------------
// Page Switching
// -----------------------------------------------------------------------------
function switchPageContent (elem) {
    let linkName = $(elem).html();
    var file = "html/" + linkName.toLowerCase().replace(" ", "_") + ".html";
    $.ajax({
        type: "GET",
        url: file,
        success: function (result) {
            $("main").html(result);
        },
        error: function (jqXHR) {
            $("main").html(jqXHR.responseText);
        },
        complete: function () { // Runs after error/success
            $("nav.bottom ul li a.active").removeClass("active");
            $(elem).addClass("active"); // Navigation links are always updated
                // regardless of success. Improves appeared responsiveness
        }
    });
}

$("nav.bottom ul li a").click(function () {
    switchPageContent(this);
});