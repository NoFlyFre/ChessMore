function onDragStart (source, piece, position, orientation) {
    if (game_status || (turn === "w" && piece.search(/^b/) !== -1) ||
        (turn === "b" && piece.search(/^w/) !== -1) || turn != orientation[0]) {
        return false;
    }
}

//funzione timer - DA TESTARE
let boolTimer = true; //se è a true, significa che il timer selezionato è timer1, altrimenti è timer2
let minutiTimer1 = 3;
let secondiTimer1 = 0;
let minutiTimer2 = 3;
let secondiTimer2 = 0;
let order = JSON.parse(document.getElementById('ordine').textContent);

function countDown(Timer) {
  if (secondiTimer1 || minutiTimer1 && secondiTimer2 || minutiTimer2) {
    setTimeout(countDown, 1000);
  }
  if (Timer) {
    secondiTimer1 -= 1;
    if (secondiTimer1 < 0) {
      minutiTimer1 -= 1;
      secondiTimer1 = 59;
    }
  }
  else {
    secondiTimer2 -= 1;
    if (secondiTimer2 < 0) {
      minutiTimer2 -= 1;
      secondiTimer2 = 59;
    }
  }
}
countDown(boolTimer);

function onDrop (source, target, piece, newPos, oldPos, orientation, boolTimer) {
    if((target[1] === '8' && piece == 'wP') || (target[1] === '1' && piece === 'bP')){
        let prom = prompt("In quale pezzo vorresti promuovere il pedone?\nScrivi la lettera 'q' per la donna, 'n' per" + " il cavallo, 'b' per l'alfiere e 'r' per la torre");
        send_move(source, target, prom)
    }
    send_move(source, target, "");
    if (boolTimer) {
      boolTimer = false;
      countDown(boolTimer);
    }
    else {
      boolTimer = true;
      countDown(boolTimer);
    }
}

function check_status (fen) {
    board.position(fen);
    switch(game_status){
        case "checkmate":
            let winner = "bianchi";
            if(turn === 'w')
                winner = "neri";
            alert("La partita è finita! Il vincitore è il giocatore con i pezzi " + winner);
            break;
        case "stalemate":
            alert("La partita è finita in pareggio per stallo!")
            break;
        case "insufficient":
            alert("La partita è finita in pareggio per posizione morta!")
            break;
        case "var_draw":
            alert("La partita è finita in pareggio per una regola della variante!")
            break;
        case "var_loss":
            let winner2 = "bianchi"
            if(turn === 'w')
                winner2 = "neri"
            alert("La partita è finita per una regola della variante! Il vincitore è il giocatore con i pezzi " + winner2)
            break;
    }
}

function pieceTheme (piece) {
    return "{% static '/multiplayer_chess/chessboardjs-1.0.0/img/chesspieces/wikipedia/' %}" + piece + '.png'; }

let orientation = 'white';
  if (order == 2) {
    orientation = 'black';
    boolTimer = false;
  }


const socket = new WebSocket('ws://' + window.location.host + '/ws/chessws/' + "{{room_number}}" + "/" + "{{variant}}" + "/");
console.log(socket);

let config = {
    orientation: orientation,
    draggable: true,
    pieceTheme: pieceTheme,
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: check_status
};

let board;
let turn;

fetch("get_position/").then(response => response.json()).then(data => {
    config.position = data.fen
    turn = data.turn
    board = ChessBoard('myBoard', config);
}).catch(error => console.error(error));

let game_status = "";
let count = 1;

socket.onmessage = function(e){
    const data = JSON.parse(e.data);
    if(data.type == 'game_move'){
        game_receive(data);
    }
    else {
        message_receive(data);
    }
};

function game_receive(data){
    game_status = data.status;
    turn = data.turn;
    check_status(data.fen);
    store_move(data.last_move, data.result);
}

function message_receive(data){
    if (data.type === "connection_established") {
        return;
    }
    let div = document.createElement("div");
    div.innerHTML = data.username + ": " + data.message;
    document.querySelector('#chat-message-container').appendChild(div);
}

function send_move(source, target, prom){
    let obj = new Object();
    obj.move = source + target + prom;
    obj.type = 'game_move';
    let string = JSON.stringify(obj);
    socket.send(string);
}

function store_move(move, result) {
    if (result == 'success') {
        const moveContainer = document.getElementById('move-container');
        const moveElement = document.createElement('p');
        const moveText = document.createTextNode(move);
        const moveSpan = document.createElement('span');
        moveSpan.appendChild(moveText);
        moveElement.appendChild(moveSpan);
        moveElement.classList.add('bg-dark');
        moveContainer.appendChild(moveElement);
    }
}

document.querySelector('#chat-message-submit').onclick = function(e){
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    const userName = JSON.parse(document.getElementById('username').textContent);
    socket.send(JSON.stringify({
        'type': 'messaggio',
        'message': message,
        'username': userName
    }));
    messageInputDom.value = '';
}

$(document).ready(function () {
  $('#modalePromozione').modal('hide');
        $("#myInput").on("click", function () {
            $('#modaleAbbandono').modal('hide');
            $('body').removeClass('modal-open');
            $('.modal-backdrop').remove();
        });
    });
