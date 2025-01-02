var domCurrent = null;
var domTitle = null;
var domThumbnail = null;
var domNextList = null;
var domForm = null;

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
        var j = -1;
        let tracks = Array.from(domNextList.querySelectorAll("li"));
        tracks.forEach(e => domNextList.removeChild(e));
        for (var i=1; i < queue.length; i++){
            let item = document.createElement("li");
            let trackId = document.createElement("span");
            let trackTitle = document.createElement("span");

            trackId.append(1 + i); // start in 2 (1 is current)
            trackTitle.append(queue[i].title);

            trackTitle.classList.add("track-title");
            trackId.classList.add("track-no");

            item.appendChild(trackId);
            item.appendChild(trackTitle);
            domNextList.appendChild(item);
        }
        playlist.classList.remove("undefined");
    } else {
        playlist.classList.add("undefined");
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
        updateList(json);
    });
}

function onLoad() {
    // Get and cache DOM elements
    domCurrent = document.getElementById("current");
    domTitle = document.querySelector("#current .track-title");
    domThumbnail = document.querySelector("#current img");
    domNextList = document.querySelector("#playlist ul");
    domForm = document.getElementById("search");

    // Replace form submit action to avoid reloading the page
    domForm.addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent submitting the form
        doSubmit(); // Invoke custom HTTP request
    });

    // Subscribe to server-sent song change events
    const evtSource = new EventSource("/changes");
    evtSource.onmessage = function(event) {
      queue = JSON.parse(event.data); // 'event.data' contains the new state
      etag = queue.etag;
      updateList(queue.tracks);
    }
}
