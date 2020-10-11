// Let us open a web socket
var ws = new WebSocket("ws://" + window.location.hostname + "/ws");

var xhr = new XMLHttpRequest();
var url = "http://" + window.location.hostname;

var me;

let send_btn = document.getElementById("send-btn");
let msg_input = document.getElementById("msg-input");
let chat = document.getElementById("chat");
let user_list = document.getElementById("user-list");

ws.onopen = function() {
  console.log("WebSocket connection established");

  xhr.onreadystatechange = function() { 
    if (xhr.readyState == 4 && xhr.status == 200)
      me = JSON.parse(xhr.responseText);
  }
  xhr.open("GET", url + "/chat/@me", true);
  xhr.send();
};

ws.onmessage = function (evt) { 
  var recv = JSON.parse(evt.data);
  
  switch (recv.type) {
  case "message":
	chat.innerHTML += "<p><strong>" + (recv.author.uuid == me.uuid ? "you" : recv.author.username) + ":</strong> " + recv.msg + "</p>";
	break;
  case "join":
	chat.innerHTML += "<p><i><strong>" + recv.user.username + "</strong> joined the chat </i></p>";
  user_list.innerHTML += "<li id=\"" + recv.user.uuid + "\">" + recv.user.username + "</li>";
	break;
  case "leave":
	chat.innerHTML += "<p><i><strong>" + recv.user.username + "</strong> left the chat </i></p>";
  document.getElementById(recv.user.uuid).remove();
	break;
  }

  chat.scrollTop = chat.scrollHeight;
};

ws.onclose = function() { 
  
  // websocket is closed.
  console.log("Connection is closed..."); 
};

// Execute a function when the user releases a key on the keyboard
msg_input.addEventListener("keyup", function(event) {
  // Number 13 is the "Enter" key on the keyboard
  if (event.keyCode === 13) {
    // Cancel the default action, if needed
    event.preventDefault();
    // Trigger the button element with a click
    send_btn.click();
  }
});

send_btn.onclick = function() {
	if (msg_input.value === "") {
		return;
	}
  xhr.onreadystatechange = function() { 
    if (xhr.readyState == 4 && xhr.status != 200)
      console.log("error sending message: " + xhr.statusText + " (code: " + xhr.status + ")");
  }
	xhr.open("POST", url + "/chat/send", true);
	xhr.setRequestHeader("Content-Type", "application/json");
	let msg = JSON.stringify({"msg": msg_input.value});
	xhr.send(msg);
	
	msg_input.value = "";
};
