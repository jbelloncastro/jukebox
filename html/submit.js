var domCurrent = null;
var domTitle = null;
var domThumbnail = null;
var domNextTable = null;
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
        var r = new Array();
        var j = -1;
        r[++j] = "<tr><th>Id</th><th>Title</th></tr>";
        for (var i=1; i < queue.length; i++){
            r[++j] = '<tr><td>';
            r[++j] = 1 + i; // start in 2 (1 is current)
            r[++j] = '</td><td>';
            r[++j] = queue[i].title;
            r[++j] = '</td></tr>';
        }
        domNextTable.innerHTML = r.join('');
        playlist.classList.remove("undefined");
    } else {
        playlist.classList.add("undefined");
    }
}

function doSubmit() {
    var url = "/tracks";
    var method = "POST";
    // FIXME: add quotes for a valid json string
    var postData = document.getElementById("query").value

    var shouldBeAsync = true;
    var request = new XMLHttpRequest();

    // What we will do when the server responds.
    request.onload = function () {
        if (request.status == 200) {
            queue = JSON.parse(request.responseText);
            updateList(queue);
        }
    }

    // Send POST request
    request.open(method, url, shouldBeAsync);
    request.setRequestHeader("Content-Type", "application/json");
    request.send(postData);
}

function onLoad() {
    // Get and cache DOM elements
    domCurrent = document.getElementById("current");
    domTitle = document.getElementById("title");
    domThumbnail = document.getElementById("thumbnail");
    domNextTable = document.getElementById("next");
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
      updateList(queue);
    }
}
