console.log("🔥 chat.js loaded");

const sendBtn = document.getElementById("sendBtn");
const userInput = document.getElementById("userInput");
const chatBox = document.getElementById("chatBox");

sendBtn.addEventListener("click", sendMessage);

function sendMessage() {
    const message = userInput.value.trim();
    if (message === "") return;

    chatBox.innerHTML += `<div class="user"><b>You:</b> ${message}</div>`;
    userInput.value = "";

    fetch("/ai-chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: message })
    })
    .then(res => res.json())
    .then(data => {
        chatBox.innerHTML += `<div class="bot"><b>Bot:</b> ${data.reply}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => {
        console.error(err);
        chatBox.innerHTML += `<div class="bot">❌ Error connecting to bot</div>`;
    });
}
