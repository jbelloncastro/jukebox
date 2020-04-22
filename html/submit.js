function doSubmit() {
    var url = "/tracks";
    var method = "POST";
    var postData = document.getElementById("query").value

    var shouldBeAsync = true;
    var request = new XMLHttpRequest();

    // What we will do when the server responds.
    request.onload = function () {
        // You can get all kinds of information about the HTTP response.
        var status = request.status; // HTTP response status, e.g., 200 for "200 OK"
        var data = request.responseText; // Returned data, e.g., an HTML document.
    }

    request.open(method, url, shouldBeAsync);
    request.setRequestHeader("Content-Type", "application/json");
    request.send(postData);
}

function onLoad() {
    // Replace form submit action to avoid reloading the page
    var form = document.getElementById("search");
    form.addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent submitting the form
        doSubmit();
    });

    // Subscribe to server-sent song change events
    const evtSource = new EventSource("/changes");
    evtSource.onmessage = function(event) {
      // 'event.data' contains the new queue state
      /*
      const newElement = document.createElement("li");
      const eventList = document.getElementById("list");

      newElement.innerHTML = "message: " + event.data;
      eventList.appendChild(newElement);
      */

      // FIXME For now just refresh the page to get it updated
      location.reload()
    }
}
