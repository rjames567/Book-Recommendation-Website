// -----------------------------------------------------------------------------
// Global Variables/Constants
// -----------------------------------------------------------------------------
let disablePopupCancel = false;
let sessionID = null; // Easier to use, allows for if (sessionID)

// -----------------------------------------------------------------------------
// String Manipulation
// -----------------------------------------------------------------------------
// https://stackoverflow.com/a/6475125/21124864
String.prototype.toTitleCase = function () {
    let str = this.replace(/([^\W_]+[^\s-]*) */g, function (txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
    return str;
}

// -----------------------------------------------------------------------------
// URL Manipulation
// -----------------------------------------------------------------------------
function changePageURI (linkName) {
    let newURI;
    if (linkName == "Home") {
        newURI = "/";
    } else {
        newURI = linkName.toLowerCase().replace(" ", "-");
    }
    history.pushState({urlPath: newURI},"", newURI);
}

function getLinkNameByURI () { // Convert URI to navigation link text.
    let uri = window.location.pathname.replace("-", " ");
    // Replace underscores with spaces
    return uri.slice(1).toTitleCase();
        // Remove leading slash, and convert to title case.
}

// JavaScript for Web Developers    ISBN: 978-1-119-36644-7
function addGetParameter (url, name, value) {
    url += (url.indexOf("?") == -1 ? "?" : "&");
    url += `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;
    return url;
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
    let file = "html/" + linkName.toLowerCase().replace(" ", "_") + ".html";
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
        hideSignUpAlert(); // Hide popup first then alert to improve perceived
            // responsiveness
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
    elem.show(); // This order so there is not a delay - minimal so not vital
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
    let password1 = $(".account-popups #sign-up input[name=password]").val();
    let password2 = $(".account-popups #sign-up input[name=password-repeat]").val();
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
        type: "GET",
        url: addGetParameter("cgi-bin/my_books/get_lists", "session_id", sessionID),
        success: function (result) {
            var firstElem;
            $(".navigation ul li:not('.template') a").remove();
            let length = Object.keys(result).length;
            for (let i = 0, temp, firstElem; i < length; i++) {
                $(".navigation ul li.template a").html(result[i]);
                temp = $(".navigation ul li.template").clone().removeClass("template").appendTo(".navigation ul");
                if (i == 0) {
                    firstElem = temp.find("a");
                }
            }
            assignReadingListNavigationHandlers();
            $(firstElem).trigger("click");
        },
        error: function (result, jqXHR) {
            alert(result["success"] + "    " + result["message"]);
        }
    });
}

function assignReadingListNavigationHandlers () {
    $(".navigation ul li a").click(function () {
        $(".navigation ul li a.active").removeClass("active")
        $(this).addClass("active");
        let listName = $(this).html();

        var requestURL = "cgi-bin/my_books/get_list_entries";
        requestURL = addGetParameter(requestURL, "session_id", sessionID)
        requestURL = addGetParameter(requestURL, "list_name", listName)
        $.ajax({
            type: "GET",
            url: requestURL,
            success: function (result) {
                $(".container .entries .book:not('.template')").remove();
                    // Remove existing entries so only new ones are shown.

                if (result["button"]) {
                    $(".container .entries .book.template .actions .read").show()
                    // incase it was hidden by previous action
                    $(".container .entries .book.template .actions .read .reading-list-manipulation").html(result["button"])
                } else {
                    $(".container .entries .book.template .actions .read").hide()
                }

                let books = result["books"];
                for (let i = 0; i < books.length; i++) {
                    let averageRating = books[i]["average_rating"];
                    $(".container .entries .book.template .title").html(books[i]["title"]);
                    $(".container .entries .book.template .author").html(books[i]["author"]);
                    $(".container .entries .book.template .date-added").html(books[i]["date_added"]);
                    $(".container .entries .book.template .synopsis").html(books[i]["synopsis"]);
                    $(".container .entries .book.template .about-review .average-review").html(averageRating);
                    $(".container .entries .book.template .about-review span.num-review").html(books[i]["num_reviews"]);
                    $(".container .entries .book.template .cover img").attr("src", books[i]["cover"]);

                    let icons = $(".container .entries .book.template .rating-container i");
                    let numFull = Math.trunc(averageRating);
                    for (let i = 0; i < numFull; i++) {
                        $(icons[i]).removeClass().addClass("fa fa-star"); // Removes all classes first. This is easier
                        // as it then does not need to worry about removing the two other possibilities. Does mean
                        // fa needs to be added as well
                    }
                    if (numFull != averageRating) {
                        $(icons[numFull]).removeClass().addClass("fa fa-star-half-o");
                        numFull += 1;
                    }
                    for (let i = numFull; i < 5; i++) {
                        $(icons[i]).removeClass().addClass("fa fa-star-o");
                    }

                    $(".container .entries .book.template ol li:not('.template')").remove();
                        // Remove any genres from previous entry.
                    for (let k in books[i]["genres"]) {
                        $(".container .entries .book.template ol li.template").find("a").html(books[i]["genres"][k]);
                        $(".container .entries .book.template ol li.template").clone().removeClass("template").appendTo(".container .entries .book.template ol");
                    }

                    $(".container .entries .book.template").clone().removeClass("template").appendTo(".container .entries");

                // Afterwards for appeared loading speed
                    let newURI = ("#" + listName).toTitleCase().split(" ").join("");
                    // Convert Name to title case, then remove ALL spaces
                    // which is why .replace is not used, and add a hashtag to
                    // use a bookmark in the search bar.
                history.pushState({urlPath: newURI},"", newURI);
                }
                assignDeleteHandlers(listName); // Assign delete handlers to remove entries
                assignMovementHandlers(listName);
            },
            error: function (jqXHR) {
                alert(jqXHR.status + " "+ jqXHR.responseText);
            }
        });
    });
}

function assignDeleteHandlers (listName) {
    $(".container .entries .book button.delete").click(function () {
        let book = $(this).closest("div.book");
        $.ajax({
            type: "POST",
            url: "cgi-bin/my_books/remove_list_entry",
            data: JSON.stringify({
                "list_name": listName,
                "book_title": $(book).find(".title").html(),
                "session_id": sessionID
            }),
            success: function (result) {
                $(book).fadeOut(500); // Hide the entry from the list
            },
            error: function (jqXHR) {
                alert(jqXHR.status + " "+ jqXHR.responseText);
            }
        });
    });
}

function assignMovementHandlers (listName) {
    $(".container .entries .book button.read").click(function () {
        let book = $(this).closest("div.book");
        $.ajax({
            type: "POST",
            url: "cgi-bin/my_books/move_list_entry",
            data: JSON.stringify({
                "list_name": listName,
                "book_title": $(book).find(".title").html(),
                "button_name": $(book).find(".reading-list-manipulation").html(),
                "session_id": sessionID
            }),
            success: function (result) {
                $(book).fadeOut(500); // Hide the entry from the list
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
    let target = window.location.pathname;
    switchPageContent(null, getLinkNameByURI());
})