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
        newURI = "/" + linkName.toLowerCase().replace(" ", "-");
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
    let file = "/html/" + linkName.toLowerCase().replace(" ", "_") + ".html";
    changePageContent(file, true, elem, linkName);
    changePageURI(linkName);
}

function reloadCurrentPage () {
    let target_arr = getLinkNameByURI().split("/");
    let target = target_arr[0];
    if (target == "Genre") { // Target is in title case
        switchGenrePage(target_arr[1]);
    } else if (target == "Book") {
        switchBookPage(decodeURI(target_arr[1])); //  Needs to be decoded; as on the refresh, any spaces have character
        // codes in, so would be replaced. This avoids double encoding the URL.
    } else { // Manually check the others as they url switching is unnecessary
        switchPageContent(null, getLinkNameByURI());
    }
}

function changePageContent (file, async, elem=null, linkName=null) {
    // Elem and linkName must BOTH be specified, or BOTH must not be specified.
    // Async specifies whether the request is synchronous (false) or asynchronous (true)
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
            // regardless of success. Improves appeared responsiveness.
            currentPageFunction(linkName);
            $(window).scrollTop(0); // Move user to the top of the window
            assignGenreNavigationHandlers(); // Needs to be in this function as it needs to reassign it based upon the page
            // content.
            assignBookNavigationHandlers(); // Needs to be in this function as it needs to reassign it based upon the page
            // content.
        },
        async: async
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
        $("header nav.top ul li.account-enter").addClass("hidden");
        $("header nav.top ul li.account-exit").removeClass("hidden");
    } else {
        $("header nav.top ul li.account-enter").removeClass("hidden");
        $("header nav.top ul li.account-exit").addClass("hidden");
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
            url: "/cgi-bin/account/sign_up",
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
                    reloadCurrentPage();
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
        url: "/cgi-bin/account/sign_in",
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
                reloadCurrentPage();
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
        url: "/cgi-bin/account/sign_out",
        data: sessionID
    });
    sessionID = null; // Must come after, as sessionID is needed unaltered
    // Minimal impact on speed, as AJAX is asynchronous
    changeAccountButtons(); // Success does not matter - just improves database
    // maintainability, any non-cleared sessions will be deleted through a
    // maintenance script
    reloadCurrentPage(); // This will be slower, so is done last. This removes any user-specific page content.
});

// -----------------------------------------------------------------------------
// Reading lists
// -----------------------------------------------------------------------------
function loadMyBooks () {
    // Get list titles
    $.ajax({
        type: "GET",
        url: addGetParameter("/cgi-bin/my_books/get_lists", "session_id", sessionID),
        success: function (result) {
            $(".navigation ul li:not('.template') a").remove();
            let length = Object.keys(result).length;
            for (let i = 0; i < length; i++) {
                let item = $(".navigation ul li.template").clone().removeClass("template");
                $(item).find("a").html(result[i]["name"]);
                $(item).appendTo(".navigation ul");
                $(item).data("id", result[i]["id"])
            }
            assignReadingListNavigationHandlers();
            $(".navigation ul li").children().eq(1).trigger("click");
        },
        error: function (result, jqXHR) {
            console.log(result["success"] + "    " + result["message"]);
        }
    });
    $(".container .entries .edit-lists button.create-list").off("click"); // Remove any preexisting handlers to prevent duplicate results
    $(".container .entries .edit-lists button.create-list").click(function () {
        $(this).hide();
        $(".container .entries .edit-lists .add-container").removeClass("hidden");
    });
    $(".container .entries .edit-lists form").off("submit"); // Remove any prexisting handlers to prevent duplicate results
    $(".container .entries .edit-lists form").on("submit", function (event) {
        event.preventDefault();
        $.ajax({
            type: "POST",
            url: "/cgi-bin/my_books/create_list",
            data: JSON.stringify({
                "session_id": sessionID,
                "list_name": $(".container .entries .edit-lists form input[name=list-name]").val()
            }),
            success: function () {
                loadMyBooks();
                $(".container .entries .edit-lists form input[name=list-name]").val("");
                // Remove the entered string incase it is re-entered before page refresh.
                $(".container .entries .edit-lists .add-container").addClass("hidden");
                $(".container .entries .edit-lists button.create-list").show();
            },
            error: function (result, jqXHR) {
                console.log(result["success"] + "    " + result["message"]);
            }
        });
    });
}

function assignReadingListNavigationHandlers () {
    $(".navigation ul li a").off("click");
    $(".navigation ul li a").click(function () {
        $(".navigation ul li a.active").removeClass("active")
        $(this).addClass("active");
        let listName = $(this).html();

        let requestURL = "/cgi-bin/my_books/get_list_entries";
        requestURL = addGetParameter(requestURL, "session_id", sessionID)
        requestURL = addGetParameter(requestURL, "list_id", $(this).closest("li").data("id"))
        $.ajax({
            type: "GET",
            url: requestURL,
            success: function (result) {
                if (["Currently Reading", "Want to Read", "Have Read"].includes(listName)) {
                    $(".container .entries .edit-lists button.delete-list").hide(); // Ensure that permanent lists
                    // cannot be deleted
                } else {
                    $(".container .entries .edit-lists button.delete-list").show();
                }
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
                    let template = $(".container .entries .book.template").clone().removeClass("template");
                    $(template).find(".title").html(books[i]["title"]);
                    let author = $(template).find(".author");
                    $(author).html(books[i]["author"]);
                    $(author).data("id", books[i]["author_id"]);
                    $(template).find(".date-added").html(books[i]["date_added"]);
                    $(template).find(".synopsis").html(books[i]["synopsis"]);
                    $(template).find(".about-review .average-review").html(averageRating.toFixed(1));
                    $(template).find(".about-review span.num-review").html(books[i]["num_reviews"]);
                    $(template).find(".cover img").attr("src", books[i]["cover"]);

                    changeElemStars($(template).find(".rating-container i"), averageRating);

                    let genres = $(template).find("ol");
                    for (let k in books[i]["genres"]) {
                        let item = $(genres).find("li.template").clone().removeClass("template");
                        $(item).find("a").html(books[i]["genres"][k]);
                        $(item).appendTo(genres);
                    }

                    $(template).insertBefore(".edit-lists");
                    $(template).data("id", books[i]["id"]);

                    let newURI = ("#" + listName).toTitleCase().split(" ").join("");
                    // Convert Name to title case, then remove ALL spaces
                    // which is why .replace is not used, and add a hashtag to
                    // use a bookmark in the search bar.
                    history.pushState({urlPath: newURI},"", newURI);
                }
                assignGenreNavigationHandlers(); // Assign handlers for the genre buttons once they have loaded
                // Handlers are not kept by the clone for whatever reason.
                assignBookNavigationHandlers();
                assignDeleteHandlers(listName); // Assign delete handlers to remove entries
                assignMovementHandlers(listName, result["move_target_id"]);
                assignListDeleteHandlers(listName); // Slower, but avoids the difficulty and possible cost of finding the list Name again.
            },
            error: function (jqXHR) {
                console.log(jqXHR.status + " " + jqXHR.responseText);
            }
        });
    });
}

function assignListDeleteHandlers (listName) {
    $(".container .entries .edit-lists button.delete-list").off("click"); // Remove
    $(".container .entries .edit-lists button.delete-list").click(function () {
        $.ajax({
            type: "POST",
            url: "/cgi-bin/my_books/remove_list",
            data: JSON.stringify({
                "session_id": sessionID,
                "list_id": $(".container .navigation li a.active").parent().data("id") // ID is attached to li element
            }),
            success: loadMyBooks, // Get the new list names, and move back to the first list and get content
            error: function (jqXHR) {
                console.log(jqXHR.status + " " + jqXHR.responseText);
            }
        });
    });
}

function assignDeleteHandlers (listName) {
    $(".container .entries .book button.delete").off("click");
    $(".container .entries .book button.delete").click(function () {
        let book = $(this).closest("div.book");
        $.ajax({
            type: "POST",
            url: "/cgi-bin/my_books/remove_list_entry",
            data: JSON.stringify({
                "list_id": $(".container .navigation li a.active").parent().data("id"),
                "book_id": $(book).data("id"),
                "session_id": sessionID
            }),
            success: function (result) {
                $(book).fadeOut(500); // Hide the entry from the list
            },
            error: function (jqXHR) {
                console.log(jqXHR.status + " " + jqXHR.responseText);
            }
        });
    });
}

function assignMovementHandlers (listName, id) {
    $(".container .entries .book button.read").off("click");
    $(".container .entries .book button.read").data("target_id", id);
    $(".container .entries .book button.read").click(function () {
        let book = $(this).closest("div.book");
        $.ajax({
            type: "POST",
            url: "/cgi-bin/my_books/move_list_entry",
            data: JSON.stringify({
                "list_id": $(".container .navigation li a.active").parent().data("id"),
                "book_id": $(book).data("id"),
                "target_list_id": $(this).data("target_id"),
                "session_id": sessionID
            }),
            success: function (result) {
                $(book).fadeOut(500); // Hide the entry from the list
            },
            error: function (jqXHR) {
                console.log(jqXHR.status + " " + jqXHR.responseText);
            }
        });
    });
}

// -----------------------------------------------------------------------------
// Genres
// -----------------------------------------------------------------------------
function assignGenreNavigationHandlers () {
    $(".genre-button").off("click");
    $(".genre-button").click(function (event) {
        switchGenrePage($(this).html());
    });
}

function switchGenrePage (genre) {
    $.ajax({
        type: "GET",
        url: addGetParameter("/cgi-bin/genres/about_data", "genre_name", genre),
        success: function (result) {
            changePageContent("/html/genre.html", false); // Must be synchronous, otherwise subsequent
            // population of the template the request supplies may fail, as it may not arrive in time.
            $(".genre-name").html(result["name"]);
            $(".about").html(result["about"]);
            let books = result["books"];
            for (let i = 0; i < Object.keys(books).length; i++) {
                let item = $(".book-summary.template").clone().removeClass("template");
                $(item).find(".title").html(books[i]["title"]);
                $(item).find(".author").html(books[i]["author"]);
                $(item).find("img").attr("src", books[i]["cover"]);
                $(item).appendTo(".genre-book-items");
                $(item).data("id", books[i]["id"]);
            }
            assignBookNavigationHandlers(true); // Assign navigation for the book summaries.
        },
        error: function (jqXHR) {
            $("main").html(jqXHR.responseText); // Fills in the main body with 404 error message
            // FIXME Fix not changing active link on AJAX fail
        },
        complete: function () {
            changePageURI("genre/" + genre); // Update page URL to point to the new genre and allow for refreshing
            // Last as it is least likely to be seen, so appears smoother
        }
    });
}

// -----------------------------------------------------------------------------
// Book pages
// -----------------------------------------------------------------------------
function assignBookNavigationHandlers (summary=false) {
    // If the link is an entire div, with an image, title etc, it needs to navigate down the DOM to find the title
    $(".book-button").off("click");
    $(".book-button").click(function () {
        let book_id;
        if (summary) {
            book_id = $(this).closest(".book-summary").data("id");
        } else {
            book_id = $(this).closest(".book").data("id");
        }
        switchBookPage(book_id);
    });
}

function switchBookPage (book_id) {
    let request_url = addGetParameter("/cgi-bin/books/about_data", "book_id", book_id);
    request_url = addGetParameter(request_url, "session_id", sessionID);
    $.ajax({
        type: "GET",
        url: request_url,
        success: function (result) {
            changePageContent("/html/book.html", false); // Must be synchronous, otherwise subsequent
            // population of the template the request supplies may fail, as it may not arrive in time.

            $(".book-about .title").html(result["title"]);
            $(".book-about .synopsis").html(result["synopsis"]);
            $(".book-about img.cover").attr("src", result["cover_image"]);
            $(".book-about .isbn").html(result["isbn"]);
            $(".book-about .publish-date").html(result["release_date"]);

            let genres = result["genres"]
            for (let i = 0; i < Object.keys(genres).length; i++) {
                $(".book-about .genres li.template a").html(genres[i]);
                $(".book-about .genres li.template").clone().removeClass("template").appendTo(".book-about .genres ol");
            }

            let numWantRead = result["num_want_read"];
            if (numWantRead == 1) {
                $(".book-about .book-stats .num-want-read .person-qualifier").html("person");
            }
            let numReading = result["num_reading"];
            if (numReading == 1) {
                $(".book-about .book-stats .num-reading .person-qualifier").html("person");
            }
            let numRead = result["num_read"];
            if (numRead == 1) {
                $(".book-about .book-stats .num-read .person-qualifier").html("person has");
            } // Other option is the default as it is hardcoded in the HTML
            $(".book-about .book-stats .num-want-read .value").html(numWantRead);
            $(".book-about .book-stats .num-reading .value").html(numReading);
            $(".book-about .book-stats .num-read .value").html(numRead);

            let author = $(".book-about .author");
            $(author).html(result["author"]);
            $(author).data("id", result["author_id"])

            if (result["author_following"]) {
                $(".book-about .author-about .follow-author").addClass("hidden");
                $(".book-about .author-about .unfollow-author").removeClass("hidden");
            } else {
                $(".book-about .author-about .unfollow-author").addClass("hidden");
                $(".book-about .author-about .follow-author").removeClass("hidden");
            }

            $(".book-about .author-about .num-followers").html(result["author_number_followers"]); // Keep in here
            // rather than use the other function to help reduce the amount requests the client sends, and reduce
            // server load, and send the number as a response to the follow/unfollow request
            $(".book-about .author-about .about").html(result["author_about"]);

            $(".book-about .average-review").html(result["average_rating"]);
            changeElemStars($(".book-about .top-container .rating i"), result["average_rating"]);
            changeElemStars($(".book-about .reviews .average-review-container i"), result["average_rating"]);
            let numRatings = result["num_ratings"]
            $(".book-about .num-review").html(numRatings);
            $(".book-about .review-distribution .bar#5-star .number").html(result["num_5_stars"]);
            $(".book-about .review-distribution .bar#4-star .number").html(result["num_4_stars"]);
            $(".book-about .review-distribution .bar#3-star .number").html(result["num_3_stars"]);
            $(".book-about .review-distribution .bar#2-star .number").html(result["num_2_stars"]);
            $(".book-about .review-distribution .bar#1-star .number").html(result["num_1_star"]);

            numRatings = Math.max(numRatings, 1); // If numRatings is 0, it changes it to 1, which does not affect the
            // percentages but avoids 0 division errors.
            let percentage = ((result["num_5_stars"] / numRatings) * 100)
            $(".book-about .review-distribution .bar#5-star .percentage").html(percentage.toFixed(2));
            $(".book-about .review-distribution .bar#5-star meter").val(percentage);
            percentage = ((result["num_4_stars"] / numRatings) * 100)
            $(".book-about .review-distribution .bar#4-star .percentage").html(percentage.toFixed(2));
            $(".book-about .review-distribution .bar#4-star meter").val(percentage);
            percentage = ((result["num_3_stars"] / numRatings) * 100)
            $(".book-about .review-distribution .bar#3-star .percentage").html(percentage.toFixed(2));
            $(".book-about .review-distribution .bar#3-star meter").val(percentage);
            percentage = ((result["num_2_stars"] / numRatings) * 100)
            $(".book-about .review-distribution .bar#2-star .percentage").html(percentage.toFixed(2));
            $(".book-about .review-distribution .bar#2-star meter").val(percentage);
            percentage = ((result["num_1_star"] / numRatings) * 100)
            $(".book-about .review-distribution .bar#1-star .percentage").html(percentage.toFixed(2));
            $(".book-about .review-distribution .bar#1-star meter").val(percentage);

            $(".book-about a.purchase_link").attr("href", result["purchase_link"])

            let reviews = result["reviews"];
            for (let i = 0; i < Object.keys(reviews).length; i++) {
                let template = $(".book-about .user-reviews .review.template").clone().removeClass("template");
                $(template).data("id", reviews[i]["id"]);
                $(template).find(".username").html(reviews[i]["username"]);
                $(template).find(".date").html(reviews[i]["date_added"]);
                if (reviews[i]["summary"] == null) {
                    $(template).find(".summary").addClass("hidden");
                } else {
                    $(template).find(".summary").removeClass("hidden");
                    $(template).find(".summary").html(reviews[i]["summary"]);
                }
                if (reviews[i]["rating_body"] == null) {
                    $(template).find(".review-body").addClass("hidden");
                } else {
                    $(template).find(".review-body").removeClass("hidden");
                    $(template).find(".review-body").html(reviews[i]["rating_body"]);
                }

                changeElemStars($(template).find(".overall-rating i"), reviews[i]["overall_rating"]);
                if (reviews[i]["plot_rating"] == null) {
                    $(template).find(".plot-rating").addClass("hidden");
                } else {
                    $(template).find(".plot-rating").removeClass("hidden");
                    changeElemStars($(template).find(".plot-rating i"), reviews[i]["plot_rating"]);
                }
                if (reviews[i]["character_rating"] == null) {
                    $(template).find(".character-rating").addClass("hidden");
                } else {
                    $(template).find(".character-rating").removeClass("hidden");
                    changeElemStars($(template).find("character-rating i"), reviews[i]["character_rating"]);
                }
                $(template).appendTo(".book-about .user-reviews");
            }

            let currentUserReview = result["current_user_review"];
            if (currentUserReview != null) {
                let existingReview = $(".book-about .user-review .existing-review").removeClass("hidden");
                $(existingReview).data("id", currentUserReview["review_id"]);
                $(".book-about .user-review .leave-review").addClass("hidden");
                if (currentUserReview["overall_rating"] == null) {
                    $(existingReview).find(".overall-rating").addClass("hidden");
                } else {
                    $(existingReview).find(".overall-rating").removeClass("hidden");
                    changeElemStars(
                        $(existingReview).find(".overall-rating i"),
                        currentUserReview["overall_rating"]
                    );
                }
                if (currentUserReview["plot-rating"] == null) {
                    $(existingReview).find(".plot-rating").addClass("hidden");
                } else {
                    $(existingReview).find(".plot-rating").removeClass("hidden");
                    changeElemStars($(existingReview).find(".plot-rating i"), currentUserReview["plot-rating"]);
                }
                if (currentUserReview["character-rating"] == null) {
                    $(existingReview).find(".character-rating").addClass("hidden");
                } else {
                    $(existingReview).find(".character-rating").removeClass("hidden");
                    changeElemStars(
                        $(existingReview).find(".character-rating i"),
                        currentUserReview["character-rating"]
                    );
                }

                if (currentUserReview["summary"] == null) {
                    $(existingReview).find(".rating-summary").addClass("hidden");
                } else {
                    $(existingReview).find(".rating-summary").removeClass("hidden");
                    $(existingReview).find(".rating-summary").html(currentUserReview["summary"]);
                }
                if (currentUserReview["rating_body"] == null) {
                    $(existingReview).find(".review-body").addClass("hidden");
                } else {
                    $(existingReview).find(".review-body").removeClass("hidden");
                    $(existingReview).find(".review-body").html(currentUserReview["rating_body"]);
                }
            }

            assignReviewDeleteButtonHandler();
            assignAuthorFollowHandlers();
            assignGenreNavigationHandlers(); // Genre navigation handlers need to be reassigned as there will be new ones
            // added
            assignChangeReadingListHandler();
        },
        error: function (jqXHR) {
            $("main").html(jqXHR.responseText); // Fills in the main body with 404 error message
            // FIXME Fix not changing active link on AJAX fail
        },
        complete: function () {
            changePageURI("book/" + book_id); // Update page URL to point to the new genre and allow for refreshing
            // Last as it is least likely to be seen, so appears smoother
        }
    });
}
function assignReviewDeleteButtonHandler () {
    $(".book-about .existing-review button.delete-review").click(function () {
        $(".book-about .user-review .leave-review").removeClass("hidden");
        let existingReview = $(".book-about .user-review .existing-review");
        $(existingReview).addClass("hidden"); // Do this before making the request, so it
        // can continue in the background for appeared responsiveness.
        $.ajax({
            type: "POST",
            url: "/cgi-bin/books/delete_review",
            data: JSON.stringify({
                "session_id": sessionID,
                "review_id": $(existingReview).data("id")
            }) // The user can only have one review of the book
        }); // The response does not matter
    });
}

function assignChangeReadingListHandler () {
    $(".book-about button.add-list").click(function () {
        $(".reading-list-selection").removeClass("hidden");
    });
}

function hideReadingListPopup () {
    $(".reading-list-selection").addClass("hidden");
}

$(window).click(function (event) {
    if ($(".reading-list-selection")[0] == event.target) {
        hideReadingListPopup();
    }
});

function assignAuthorFollowHandlers () {
    $(".book-about .author-about .follow-author").click(function () {
        // Can only follow a user if an account is known, so prompts if not signed in.
        if (sessionID) {
            $.ajax({
                type: "POST",
                url: "/cgi-bin/authors/follow_author",
                data: JSON.stringify({
                    "session_id": sessionID,
                    "author_id": $(".book-about .author").data("id")
                }),
                success: function (result) {
                    $(".book-about .author-about .follow-author").addClass("hidden");
                    $(".book-about .author-about .unfollow-author").removeClass("hidden");
                    $(".book-about .author-about .num-followers").html(result); // Update number of followers
                }
            });
        } else {
            showSignInPopup();
        }
    });
    $(".book-about .author-about .unfollow-author").click(function () {
        $.ajax({ // This cannot be shown if not signed in, so does not check
            type: "POST",
            url: "/cgi-bin/authors/unfollow_author",
            data: JSON.stringify({
                "session_id": sessionID,
                "author_id": $(".book-about .author").data("id")
            }),
            success: function (result) {
                $(".book-about .author-about .unfollow-author").addClass("hidden");
                $(".book-about .author-about .follow-author").removeClass("hidden");
                $(".book-about .author-about .num-followers").html(result); // Update number of followers
            }
        });
    });
}

// -----------------------------------------------------------------------------
// Rating stars
// -----------------------------------------------------------------------------
function changeElemStars (icons, averageRating) {
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
}

// -----------------------------------------------------------------------------
// window onload handlers
// -----------------------------------------------------------------------------
$(document).ready(function () {
    reloadCurrentPage();
})

// TODO display meta if reading list is empty