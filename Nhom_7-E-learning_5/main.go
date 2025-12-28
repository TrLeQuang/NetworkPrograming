package main

import (
	"log"
	"net/http"
	"os/exec"
	"time"

	"github.com/gorilla/websocket"
)

/*
	WebSocket Chat (GUI Web)
	- Mở http://localhost:9999 là thấy giao diện chat
	- Mở nhiều tab để test broadcast realtime
	- Khi chạy go run main.go -> tự mở trình duyệt
*/

const pageHTML = `<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>WebSocket Chat GUI</title>
  <style>
    body{font-family:system-ui,Segoe UI,Arial;margin:0;background:#0b1220;color:#e6e8ee}
    .wrap{max-width:900px;margin:24px auto;padding:16px}
    .card{background:#121a2b;border:1px solid #24304a;border-radius:14px;padding:14px;box-shadow:0 8px 30px rgba(0,0,0,.25)}
    .row{display:flex;gap:10px;flex-wrap:wrap}
    input,button{border-radius:12px;border:1px solid #2a3756;background:#0e1628;color:#e6e8ee;padding:10px 12px}
    input{flex:1;min-width:200px}
    button{cursor:pointer}
    button:hover{filter:brightness(1.08)}
    .pill{display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid #2a3756;background:#0e1628;margin-left:8px;font-size:12px;opacity:.9}
    #log{margin-top:14px;height:420px;overflow:auto;background:#0e1628;border:1px solid #24304a;border-radius:14px;padding:12px}
    .msg{padding:8px 10px;border-radius:12px;margin:8px 0;max-width:85%}
    .me{background:#1a3b2a;border:1px solid #2b6a48;margin-left:auto}
    .other{background:#1b2742;border:1px solid #2a3a62}
    .sys{background:#2a1b2a;border:1px solid #5a2a5a;opacity:.95;max-width:100%}
    .meta{font-size:12px;opacity:.75;margin-top:4px}
    .top{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <h2 style="margin:0">WebSocket Chat GUI</h2>
      <span class="pill" id="status">DISCONNECTED</span>
    </div>

    <div class="card">
      <div class="row" style="margin-bottom:10px">
        <input id="name" placeholder="Tên hiển thị (ví dụ: A, B, ...)" />
        <button id="btnConnect">Connect</button>
        <button id="btnDisconnect" disabled>Disconnect</button>
      </div>

      <div class="row">
        <input id="text" placeholder="Nhập tin nhắn rồi Enter..." />
        <button id="btnSend" disabled>Send</button>
      </div>

      <div id="log"></div>
      <div class="meta">Tip: mở 2 tab trình duyệt để test chat realtime.</div>
    </div>
  </div>

<script>
let ws = null;

const $ = (id)=>document.getElementById(id);
const statusPill = $("status");
const logBox = $("log");

function setStatus(s, ok){
  statusPill.textContent = s;
  statusPill.style.borderColor = ok ? "#2b6a48" : "#5a2a5a";
}

function append(type, who, text){
  const div = document.createElement("div");
  div.className = "msg " + type;
  const t = new Date().toLocaleTimeString();
  if(type === "sys"){
    div.innerHTML = "<b>[SYSTEM]</b> " + escapeHtml(text) + '<div class="meta">' + t + "</div>";
  }else{
    div.innerHTML = "<b>" + escapeHtml(who) + "</b>: " + escapeHtml(text) + '<div class="meta">' + t + "</div>";
  }
  logBox.appendChild(div);
  logBox.scrollTop = logBox.scrollHeight;
}

function escapeHtml(s){
  s = s || "";
  return s.replaceAll("&","&amp;")
          .replaceAll("<","&lt;")
          .replaceAll(">","&gt;")
          .replaceAll('"',"&quot;")
          .replaceAll("'","&#039;");
}

function setUI(connected){
  $("btnConnect").disabled = connected;
  $("btnDisconnect").disabled = !connected;
  $("btnSend").disabled = !connected;
  $("text").disabled = !connected;
}

function connect(){
  const proto = (location.protocol === "https:") ? "wss" : "ws";
  const url = proto + "://" + location.host + "/ws";
  ws = new WebSocket(url);

  ws.onopen = ()=>{
    setStatus("CONNECTED", true);
    setUI(true);
    append("sys","", "Connected to " + url);
  };

  ws.onmessage = (e)=>{
    const raw = e.data || "";
    const idx = raw.indexOf("|");
    if (idx >= 0){
      const who = raw.slice(0, idx);
      const msg = raw.slice(idx+1);
      const me = ($("name").value || "Me").trim();
      append(who === me ? "me" : "other", who, msg);
    } else {
      append("other","Server", raw);
    }
  };

  ws.onclose = ()=>{
    setStatus("DISCONNECTED", false);
    setUI(false);
    append("sys","", "Disconnected.");
    ws = null;
  };

  ws.onerror = ()=>{
    append("sys","", "WebSocket error.");
  };
}

function disconnect(){
  if (ws) ws.close();
}

function sendMsg(){
  if (!ws) return;
  const name = ($("name").value || "Me").trim();
  const text = ($("text").value || "").trim();
  if (!text) return;
  ws.send(name + "|" + text);
  $("text").value = "";
  $("text").focus();
}

$("btnConnect").onclick = connect;
$("btnDisconnect").onclick = disconnect;
$("btnSend").onclick = sendMsg;
$("text").addEventListener("keydown", (e)=>{
  if (e.key === "Enter") sendMsg();
});

setUI(false);
setStatus("DISCONNECTED", false);
append("sys","", "Mở 2 tab và Connect để test.");
</script>
</body>
</html>`

// ======================
// Backend: WebSocket Hub
// ======================

type Client struct {
	conn *websocket.Conn
	send chan []byte
}

type Hub struct {
	clients    map[*Client]bool
	register   chan *Client
	unregister chan *Client
	broadcast  chan []byte
}

func NewHub() *Hub {
	return &Hub{
		clients:    make(map[*Client]bool),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan []byte, 2048), // buffer giúp chịu burst tốt hơn
	}
}

func (h *Hub) Run() {
	for {
		select {
		case c := <-h.register:
			h.clients[c] = true

		case c := <-h.unregister:
			if _, ok := h.clients[c]; ok {
				delete(h.clients, c)
				close(c.send)
				_ = c.conn.Close()
			}

		case msg := <-h.broadcast:
			for c := range h.clients {
				select {
				case c.send <- msg:
				default:
					// Client quá chậm (send channel đầy) -> loại để không kéo sập hệ thống
					delete(h.clients, c)
					close(c.send)
					_ = c.conn.Close()
				}
			}
		}
	}
}

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin:     func(r *http.Request) bool { return true }, // demo đơn giản
}

func (c *Client) readPump(h *Hub) {
	defer func() { h.unregister <- c }()

	_ = c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.conn.SetPongHandler(func(string) error {
		_ = c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, msg, err := c.conn.ReadMessage()
		if err != nil {
			return
		}
		h.broadcast <- msg
	}
}

func (c *Client) writePump() {
	ticker := time.NewTicker(30 * time.Second) // ping giữ kết nối
	defer func() {
		ticker.Stop()
		_ = c.conn.Close()
	}()

	for {
		select {
		case msg, ok := <-c.send:
			_ = c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				_ = c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}
			if err := c.conn.WriteMessage(websocket.TextMessage, msg); err != nil {
				return
			}

		case <-ticker.C:
			_ = c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

func wsHandler(h *Hub) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			http.Error(w, "upgrade failed", http.StatusBadRequest)
			return
		}

		client := &Client{
			conn: conn,
			send: make(chan []byte, 256),
		}
		h.register <- client

		go client.writePump()
		go client.readPump(h)
	}
}

// Tự mở trình duyệt trên Windows
func openBrowser(url string) {
	cmd := exec.Command("cmd", "/c", "start", url)
	_ = cmd.Start()
}

func main() {
	hub := NewHub()
	go hub.Run()

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		_, _ = w.Write([]byte(pageHTML))
	})

	http.HandleFunc("/ws", wsHandler(hub))

	// Đợi server lên rồi mở web
	go func() {
		time.Sleep(500 * time.Millisecond)
		openBrowser("http://localhost:9999")
	}()

	log.Println("Open GUI: http://localhost:9999")
	log.Fatal(http.ListenAndServe(":9999", nil))
}
