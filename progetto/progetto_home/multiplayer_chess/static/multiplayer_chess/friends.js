input = document.querySelector("#friendSearch");
btnFriendSearch = document.querySelector("#friendSearchButton");
diplayContainer = document.querySelector("#searchResult");
let friend_name;
btnFriendSearch.addEventListener("click", () => {
  friend_name = input.value;

  let url = getPlayerExistsUrl(friend_name);
  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      if (!data["exists"]) {
        alert(data["msg"]);
      } else {
        displayPlayer(friend_name);
      }
    });
});

function displayPlayer(friend_name) {
  document.querySelector("#searchResultContainer").classList.remove("d-none");
  document.querySelector("#searchResultContainer").classList.add("d-flex");
  document.querySelector("#searchResultName").innerText = friend_name;
}
document.querySelector("#btnSendRequest").addEventListener("click", () => {
  let url = getSendRequestUrl(friend_name);
  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      alert(data["msg"]);
    });
});
