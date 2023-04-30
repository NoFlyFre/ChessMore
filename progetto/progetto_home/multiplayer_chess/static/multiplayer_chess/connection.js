const chatSocket = new WebSocket(
  "ws://" + window.location.host + "/ws/multiplayer_chess/home"
);

chatSocket.onmessage = function (e) {
  const data = JSON.parse(e.data);
  friend_name = data["friend_name"];
  console.log(friend_name + " wants to play");
  let choice = confirm(friend_name + " wants to play with you");
  if (choice == true) {
    window.location.assign(getFriendMatchUrl(friend_name));
  }
};
