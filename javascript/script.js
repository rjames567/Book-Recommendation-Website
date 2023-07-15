// -----------------------------------------------------------------------------
// Global Variables/Constants
// -----------------------------------------------------------------------------
var disablePopupCancel = false;

// -----------------------------------------------------------------------------
// String Manipulation
// -----------------------------------------------------------------------------
// https://stackoverflow.com/a/6475125/21124864
String.prototype.toTitleCase = function () {
    var str = this.replace(/([^\W_]+[^\s-]*) */g, function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
    return str;
}

// -----------------------------------------------------------------------------
// URL Manipulation
// -----------------------------------------------------------------------------
function changePageURI (linkName) {
    var newURI;
    if (linkName == "Home") {
        newURI = "/";
    } else {
        newURI = linkName.toLowerCase().replace(" ", "-");
    }
    history.pushState({urlPath: newURI},"", newURI);
}

function getLinkNameByURI () { // Convert URI to navigation link text.
    var uri = window.location.pathname.replace("-", " ");
        // Replace underscores with spaces
    return uri.slice(1).toTitleCase();
        // Remove leading slash, and convert to title case.
}

// -----------------------------------------------------------------------------
// Page Switching
// -----------------------------------------------------------------------------
function switchPageContent (elem, linkName) {
    // Does not switch elem to link as using links is very slow, as it needs to
        // iterate through all available link names, to find the correct one.
    if (elem) {
        linkName = $(elem).html();
    }
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
            if (elem) { // Allow for both element or link name to be used.
                changeActiveLink(elem, null);
                linkName = $(elem).html();
            } else {
                changeActiveLink(null, linkName);
            }// Navigation links are always updated
                // regardless of success. Improves appeared responsiveness
            changePageURI(linkName);
        }
    });
}

function changeActiveLink (elem, linkContent) {
    $("nav.bottom ul li a.active").removeClass("active");
    if (elem) {
        $(elem).addClass("active");
    } else {
        $("nav.bottom ul li a").each(function () {
            if ($(this).html() == linkContent) {
                $(this).addClass("active");
            }
        });
    }
}

$("nav.bottom ul li a, footer ul li a").click(function () {
    switchPageContent(this, null);
});

// -----------------------------------------------------------------------------
// Sign In/Sign Up
// -----------------------------------------------------------------------------
function hideAllSignPopups () { // Needed so cancel buttons and click-off can be
    // generalised for both.
    if (!disablePopupCancel) {
        $(".account-popups .window").hide()
    }
}

$(".account-popups button.cancel-button").click(function () {
    hideAllSignPopups();
});

$(window).click(function (event) {
    if ([$("#sign-up")[0],  $("#sign-in")[0]].includes(event.target)
            && !disablePopupCancel) {
        hideAllSignPopups();
    }
});

// -----------------------------------------------------------------------------
// Sign Up - Popup Visibility
// -----------------------------------------------------------------------------
function showSignUpPopup () {
    $(".account-popups .window#sign-up").show();
}

// -----------------------------------------------------------------------------
// Sign Up - Form submission
// -----------------------------------------------------------------------------
$(".account-popups .window#sign-up form").on("submit", function (event) {
    event.preventDefault();
    disablePopupCancel = true;
});

// -----------------------------------------------------------------------------
// Sign Up - Link Onclick handlers
// -----------------------------------------------------------------------------
$("header a#sign-up-button").click(function () {
    showSignUpPopup();
});

// -----------------------------------------------------------------------------
// Sign In - Popup Visibility
// -----------------------------------------------------------------------------
function showSignInPopup () {
    $(".account-popups .window#sign-in").show();
}

// -----------------------------------------------------------------------------
// Sign In - Form submission
// -----------------------------------------------------------------------------
$(".account-popups .window#sign-in form").on("submit", function (event) {
    event.preventDefault();
    disablePopupCancel = true;
});

// -----------------------------------------------------------------------------
// Sign In - Link Onclick handlers
// -----------------------------------------------------------------------------
$("header a#sign-in-button").click(function () {
    showSignInPopup();
});

// -----------------------------------------------------------------------------
// window onload handlers
// -----------------------------------------------------------------------------
$(document).ready(function () {
    var target = window.location.pathname;
    switchPageContent(null, getLinkNameByURI());
})