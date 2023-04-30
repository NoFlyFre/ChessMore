const pieces = {
  P: "&#9817;",
  N: "&#9816;",
  B: "&#9815;",
  R: "&#9814;",
  Q: "&#9813;",
  K: "&#9812;",

  p: "&#9823;",
  n: "&#9822;",
  b: "&#9821;",
  r: "&#9820;",
  q: "&#9819;",
  k: "&#9818;",

  ".": " ",
};
var legal_moves;
var color;
var chatSocket;
var turn;
var opponent;
var preClick = -1;
var resultModal = new bootstrap.Modal(document.getElementById("resultModal"));

if (game_type == 0) {
  chatSocket = new WebSocket(
    "ws://" + window.location.host + "/ws/multiplayer_chess/gameroom/random"
  );
} else {
  console.log("With friend");
  chatSocket = new WebSocket(
    "ws://" +
      window.location.host +
      "/ws/multiplayer_chess/gameroom/friend/" +
      friend_name
  );
}

chatSocket.onmessage = function (e) {
  const data = JSON.parse(e.data);
  console.log(data);

  if (data["type"] == 0) {
    document.getElementById("spinner").classList.add("hidden");
    color = data["color"];
    turn = data["turn"];
    opponent = data["opponent"];
    document.getElementById("opponent-name").innerText = opponent;
    updateBoard(data["board"]);
    legal_moves = data["legal_moves"];
  } else if (data["type"] == 1) {
    turn = data["turn"];
    updateBoard(data["board"]);
    legal_moves = data["legal_moves"];
    updateCaptured(data["captured"]);
    checkResult(data["result"]);
  }
};
function checkResult(result) {
  if (result === "*") {
    return;
  } else {
    if (result === "1-0" || result === "0-1") {
      document.getElementById("resultTitle").innerText = "Checkmate";
      let winner;
      if (result === "1-0") winner = 0;
      else winner = 1;

      if (winner === color) {
        document.getElementById("resultText").innerText = "You won";
      } else {
        document.getElementById("resultText").innerText = `${opponent} won`;
      }
    } else {
      document.getElementById("resultTitle").innerText = "Draw";
      document.getElementById("resultText").innerText = "Match draw";
    }
    resultModal.show();
  }
}
function updateCaptured(captured) {
  if (captured === ".") {
    return;
  }
  // if it is player's turn now then the captured piece belongs to player
  if (color == turn) {
    let captured_pieces = String(
      document.getElementById("opponent-pieces").innerHTML
    );
    console.log(typeof captured_pieces);
    captured_pieces += pieces[captured];
    document.getElementById("opponent-pieces").innerHTML = captured_pieces;
  } else {
    let captured_pieces = String(
      document.getElementById("player-pieces").innerHTML
    );
    captured_pieces += pieces[captured];
    document.getElementById("player-pieces").innerHTML = captured_pieces;
  }
}
function updateBoard(board) {
  for (let i = 0; i < 8; i++) {
    for (let j = 0; j < 8; j++) {
      cells[8 * i + j].innerHTML = pieces[board[i][j]];
    }
  }
}

for (let i = 0; i < 64; i++) {
  cells[i].addEventListener("click", function (event) {
    event.stopPropagation();
    let cellClicked = getCellStringRepresentation(i);
    let legalMovesFromThisCell = legal_moves.filter((legal_move) => {
      return legal_move.startsWith(cellClicked);
    });
    console.log(legalMovesFromThisCell);
    highlightLegalCells(legalMovesFromThisCell);

    let move = getMoveRepresentation(preClick, i);
    if (legal_moves.includes(move)) {
      console.log("Legal move");
      // send this move to server only if it is the player's turn
      if (turn == color) {
        chatSocket.send(
          JSON.stringify({
            move: move,
          })
        );
      }
    }
    preClick = i;
  });
}

function highlightLegalCells(moves) {
  for (let i = 0; i < 64; i++) {
    highlights[i].classList.add("hidden");
  }
  for (let m of moves) {
    console.log(getCellIntRepresentation(m.substring(2, 4)));
    highlights[getCellIntRepresentation(m.substring(2, 4))].classList.remove(
      "hidden"
    );
  }
}

// get cell representation from cell number i.e 57 -> (7,1) -> 'b1'
function getCellStringRepresentation(cellNo) {
  if (color != 0) {
    // black color
    cellNo = 63 - cellNo; // because the board is rotated for black player
  }
  let x = Math.floor(cellNo / 8);
  let y = cellNo % 8;
  return String.fromCharCode(97 + y).concat((8 - x).toString());
}
function getCellIntRepresentation(cellStr) {
  let x = cellStr.charCodeAt(0) - 97;
  let y = 8 - parseInt(cellStr[1]);
  n = 8 * y + x;
  if (color != 0) {
    return 63 - n;
  }
  return n;
}

function getMoveRepresentation(preClick, currClick) {
  if (preClick == -1 || preClick == 64) {
    return "None";
  }
  return getCellStringRepresentation(preClick).concat(
    getCellStringRepresentation(currClick)
  );
}

function resize_table_chess(id) {
  $(id).width("auto").height("auto");
  $(id + " td")
    .width("auto")
    .height("auto")
    .css({ "font-size": 0.1 + "em" });
  var sizT = Math.max(
    Math.max($(id).width(), $(id).height()),
    Math.min($(window).width(), $(window).height())
  );
  if ($(window).width() > $(window).height()) {
    sizT -= 100;
  } else {
    sizT -= 50;
  }
  $(id).width(sizT).height(sizT);
  var maxWH = sizT / 8; //
  $(id + " td")
    .width(maxWH)
    .height(maxWH);
  $(id + " td").css({
    maxHeight: maxWH,
  });
  $(id + " td").css({
    "font-size": Math.floor((100 * maxWH) / 16 / 1.8) / 100 + "em",
  });
}
$(window).on("load resize", function () {
  resize_table_chess("#board");
});
