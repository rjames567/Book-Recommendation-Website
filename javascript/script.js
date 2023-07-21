// -----------------------------------------------------------------------------
// Global Variables/Constants
// -----------------------------------------------------------------------------
var disablePopupCancel = false;
var sessionID = null; // Easier to use, allows for if (sessionID)

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
    if (linkName == "") {
        linkName = "Home" // If it is blank, it must be referring to the Home
            // page.
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
            currentPageFunction(linkName);
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

function currentPageFunction (link) {
    checkSignInNecessary(link);
    switch (link) {
        case "My Books":
            loadMyBooks();
            break;
    }
}

$("nav.bottom ul li a, footer ul li a").click(function () {
    switchPageContent(this, null);
});

// -----------------------------------------------------------------------------
// Sign In/Sign Up
// -----------------------------------------------------------------------------
function checkSignInNecessary (link) {
    if (["My Books", "Recommendations", "Diary"].includes(link) && !sessionID) {
        $(".account-popups .page-sign-notice").show();
        showSignInPopup();
        return true;
    }
    return false;
}

function hideAllSignPopups () { // Needed so cancel buttons and click-off can be
    // generalised for both.
    if (!disablePopupCancel) {
        $(".account-popups .window").hide()
        hideSignUpAlert(); // Hide popup first then alert to improve percieved
            // responsivness
        $(".account-popups .page-sign-notice").hide();
    }
}

$(".account-popups button.cancel-button").click(function () {
    hideAllSignPopups();
});

function changeAccountButtons () {
    if (sessionID) {
        $("header nav.top ul li.account-enter").hide();
        $("header nav.top ul li.account-exit").show();
    } else {
        $("header nav.top ul li.account-enter").show();
        $("header nav.top ul li.account-exit").hide();
    }
}

$(window).click(function (event) {
    if ([$("#sign-up")[0],  $("#sign-in")[0]].includes(event.target)
            && !disablePopupCancel) {
        hideAllSignPopups();
    }
});

// -----------------------------------------------------------------------------
// Sign In/Sign Up - Alerts
// -----------------------------------------------------------------------------
function signUpAlert (message) {
    var elem = $(".account-popups p.alert");
    elem.html(message);
    elem.show(); // This order so their is not a delay - minimal so not vital
    timeout = setTimeout(function () {
        elem.fadeOut(500); // Fade out in 1/2 seconds
    }, 8000); // Hide alert after 8 seconds
}

function hideSignUpAlert () {
    $(".account-popups p.alert").hide();
}

// -----------------------------------------------------------------------------
// Sign Up - Popup Visibility
// -----------------------------------------------------------------------------
function showSignUpPopup () {
    $(".account-popups .window#sign-in").hide(); // Hide previous popup
    $(".account-popups .window#sign-up").show();
}

// -----------------------------------------------------------------------------
// Sign Up - Form submission
// -----------------------------------------------------------------------------
$(".account-popups .window#sign-up form").on("submit", function (event) {
    event.preventDefault();
    disablePopupCancel = true;
    var password1 = $(".account-popups #sign-up input[name=password]").val();
    var password2 = $(".account-popups #sign-up input[name=password-repeat]").val();
    if (password1 != password2) {
        signUpAlert("Passwords do not match");
        disablePopupCancel = false;
    } else {
        $.ajax({
            type: "POST",
            url: "cgi-bin/account/sign_up",
            data: JSON.stringify({
                first_name: $(".account-popups #sign-up input[name=first-name]").val(),
                surname: $(".account-popups #sign-up input[name=surname]").val(),
                username: $(".account-popups #sign-up input[name=username]").val(),
                password: password1
            }),
            success: function (result) {
                disablePopupCancel = false; // Cannot go in complete, as it runs
                    // after success, so hiding the popup does not work.
                if (result["session_id"]) {
                    sessionID = result["session_id"];
                    changeAccountButtons(); // Change before it can be seen to
                        // appear smoother
                    hideAllSignPopups();
                } else {
                    signUpAlert(result["message"]);
                }
            },
            error: function () {
                // Error should only run for server-side errors
                signUpAlert("Something went wrong");
                disablePopupCancel = false;
            }
        });
    }
});

// -----------------------------------------------------------------------------
// Sign Up - Link Onclick handlers
// -----------------------------------------------------------------------------
$("a#sign-up-button").click(function () {
    showSignUpPopup();
});

// -----------------------------------------------------------------------------
// Sign In - Popup Visibility
// -----------------------------------------------------------------------------
function showSignInPopup () {
    $(".account-popups .window#sign-in").show(); // For whatever reason, only
        // hide on the showSignUpPopup is needed
}

// -----------------------------------------------------------------------------
// Sign In - Form submission
// -----------------------------------------------------------------------------
$(".account-popups .window#sign-in form").on("submit", function (event) {
    event.preventDefault();
    disablePopupCancel = true;
    $.ajax({
        type: "POST",
        url: "cgi-bin/account/sign_in",
        data: JSON.stringify({
            username: $(".account-popups #sign-in input[name=username]").val(),
            password: $(".account-popups #sign-in input[name=password]").val()
        }),
        success: function (result) {
            disablePopupCancel = false; // Cannot go in complete, as it runs
                // after success, so hiding the popup does not work.
            if (result["session_id"]) {
                sessionID = result["session_id"];
                changeAccountButtons(); // Change before it can be seen to
                    // appear smoother
                hideAllSignPopups();

            } else {
                signUpAlert(result["message"]);
            }
        },
        error: function () {
            // Error should only run for server-side errors
            signUpAlert("Something went wrong");
            disablePopupCancel = false;
        }
    });
});

// -----------------------------------------------------------------------------
// Sign In - Link Onclick handlers
// -----------------------------------------------------------------------------
$("a#sign-in-button").click(function () {
    showSignInPopup();
});

// -----------------------------------------------------------------------------
// Sign Out - Link Onclick handlers
// -----------------------------------------------------------------------------
$("header a#sign-out-button").click(function () {
    $.ajax({
        type: "POST",
        url: "cgi-bin/account/sign_out",
        data: sessionID
    });
    sessionID = null; // Must come after, as sessionID is needed unaltered
        // Minimal impact on speed, as AJAX is asynchronous
    changeAccountButtons(); // Success does not matter - just improves database
        // maintainability, any non-cleared sessions will be deleted through a
        // maintenance script
});

// -----------------------------------------------------------------------------
// Reading lists
// -----------------------------------------------------------------------------
function loadMyBooks () {
    // Get list titles
    $.ajax({
        type: "POST",
        url: "cgi-bin/my_books/get_lists",
        data: sessionID,
        success: function (result) {
            $(".navigation ul li:not('.template') a").remove();
            var length = Object.keys(result).length;
            for (var i = 0; i < length; i++) {
                $(".navigation ul li.template a").html(result[i]);
                temp = $(".navigation ul li.template").clone().removeClass("template").appendTo(".navigation ul");
                if (i == 0) {
                    firstElem = temp.find("a");
                }
            }
            assignReadingListNavigationHandlers();
            $(firstElem).trigger("click");
        },
        error: function (jqXHR) {
            alert(result["success"] + "    " + result["message"]);
        }
    });
}

function assignReadingListNavigationHandlers () {
    $(".navigation ul li a").click(function () {
        $(".navigation ul li a.active").removeClass("active")
        $(this).addClass("active");
        var listName = $(this).html();

        $.ajax({
            type: "POST", // Post as session ids shouldn't be exposed
            url: "cgi-bin/my_books/get_list_entries",
            data: JSON.stringify({
                "session_id": sessionID,
                "list_name": listName
            }),
            success: function (result) {
                var newURI = ("#" + listName).toTitleCase().split(" ").join("");
                    // Convert Name to title case, then remove ALL spaces
                    // which is why .replace is not used, and add a hashtag to
                    // use a bookmark in the search bar.
                history.pushState({urlPath: newURI},"", newURI);
                $(".container .entries .book:not('.template')").remove();
                    // Remove existing entries so only new ones are shown.
                var books = result["books"];
                for (var i = 0; i < books.length; i++) {
                    $(".container .entries .book.template .title").html(books[i]["title"]);
                    $(".container .entries .book.template .author").html(books[i]["author"]);
                    $(".container .entries .book.template .date-added").html(books[i]["date_added"]);
                    $(".container .entries .book.template .synopsis").html(books[i]["synopsis"]);
                    $(".container .entries .book.template .cover img").attr("src", books[i]["cover"]);
                    $(".container .entries .book.template").clone().removeClass("template").appendTo(".container .entries");
                }
            },
            error: function (jqXHR) {
                alert(jqXHR.status + " "+ jqXHR.responseText);
            }
        });
    });
}

// -----------------------------------------------------------------------------
// window onload handlers
// -----------------------------------------------------------------------------
$(document).ready(function () {
    var target = window.location.pathname;
    switchPageContent(null, getLinkNameByURI());
})