var domCurrent = null;
var domTitle = null;
var domThumbnail = null;
var domNextList = null;
var domListTemplate = null;
var domForm = null;
var evtSource = null;

// Resets #current and #playlist div elements with the latest values of
// current and following variables
// Assume all the dom elements have been queried (onLoad() was called)
function updateList(queue) {
    if (queue.length > 0 && queue[0] != null) {
        domTitle.innerHTML = queue[0].title;
        domThumbnail.src = queue[0].caption;
        domCurrent.classList.remove("undefined");
    } else {
        domCurrent.classList.add("undefined");
    }

    if (queue.length > 1) {
        let newList = [];
        for (var i=1; i < queue.length; i++){
            let item = domListTemplate.content.cloneNode(true);

            let trackId, trackTitle;
            [trackNo, trackTitle] = item.querySelectorAll("span");

            trackNo.textContent = 1 + i; // start in 2 (1 is current)
            trackTitle.textContent = queue[i].title;

            newList.push(item);
        }
        domNextList.replaceChildren(...newList);
        domNextList.classList.remove("undefined");

    } else {
        domNextList.classList.add("undefined");
    }
}

function doSubmit() {
    var url = "/tracks";
    var method = "POST";
    var postData = '"' + document.getElementById("query").value + '"';
    if (postData.length == 0)
        return;

    // Send POST request
    fetch(url, {
        "method": "POST",
        "headers": new Headers({"Content-Type": "application/json"}),
        "body": postData
    }).then((response) => {
        if (response.ok)
            return response.json();
        else
            throw response;
    }).then((json) => {
        // ignored because we receive the update via EventSource
        // updateList(json);
    });
}

// Subscribe to server-sent song change events
function setupSSE() {
    evtSource = new EventSource("/changes");

    evtSource.addEventListener("list-update", (event) => {
      var queue = JSON.parse(event.data); // 'event.data' contains the new state
      updateList(queue.tracks);
    });

    evtSource.addEventListener("error", (err) => {
        console.error("EventSource failed:", err);
        evtSource.close()
        // setupSSE()
    });
}

function onLoad() {
    // Get and cache DOM elements
    domCurrent = document.getElementById("current");
    domTitle = document.querySelector("#current .track-title");
    domThumbnail = document.querySelector("#current img");
    domNextList = document.getElementById("playlist");
    domListTemplate = document.getElementById("playlist-entry");
    domForm = document.getElementById("search");

    // Replace form submit action to avoid reloading the page
    domForm.addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent submitting the form
        doSubmit(); // Invoke custom HTTP request
    });

    setupSSE();
}
